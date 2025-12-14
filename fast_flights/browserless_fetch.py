import os
import asyncio
import re
import base64
from typing import Any, Optional, List, Dict


def _extract_segments_from_google_tfs(url: str) -> Optional[List[Dict]]:
    """Extract flight segments from Google's TFS parameter in URL.

    When user clicks on a flight, Google updates the URL with a TFS that contains
    the exact flight segments including dates. This is more reliable than parsing HTML.

    Returns:
        List of segment dicts with keys: airline, flight_number, from, to, date
        Returns None if extraction fails.
    """
    try:
        # Extract TFS from URL
        tfs_match = re.search(r'tfs=([^&]+)', url)
        if not tfs_match:
            return None

        tfs_str = tfs_match.group(1)

        # Add padding for base64 decoding
        tfs_padded = tfs_str + "=" * ((4 - len(tfs_str) % 4) % 4)
        tfs_bytes = base64.urlsafe_b64decode(tfs_padded)

        # Import protobuf module
        from . import flights_pb2 as PB

        # Parse as ReturnFlightQuery
        query = PB.ReturnFlightQuery()
        query.ParseFromString(tfs_bytes)

        # Extract segments from the first leg
        if not query.legs:
            return None

        segments = []
        for sf in query.legs[0].selected_flight:
            segments.append({
                'airline': sf.airline,
                'flight_number': sf.flight_number,
                'from': sf.from_airport,
                'to': sf.to_airport,
                'date': sf.date
            })

        return segments if segments else None

    except Exception as e:
        if os.environ.get('DEBUG_FLIGHT_DETAILS'):
            print(f"DEBUG: Error extracting segments from TFS: {e}")
        return None


def fetch_flight_details(
    params: dict,
    airline: str,
    departure_time: str,
    price: str,
    origin: str = "",
    destination: str = "",
    date: str = ""
) -> Optional[Dict]:
    """Click on a specific flight card to extract flight numbers.

    This is used when HTML parsing doesn't provide flight numbers (e.g., browserless fallback).
    It finds the flight by matching airline, departure time, and price, then clicks to expand
    and extracts the flight numbers from the detail view.

    For roundtrip searches, this function creates a ONE-WAY search URL to get outbound flight
    details, since clicking on a roundtrip outbound only shows return options.

    Args:
        params: The search parameters (tfs, hl, tfu, curr)
        airline: Airline name(s) from the flight (e.g., "Turkish Airlines" or "Lufthansa, SunExpress")
        departure_time: Departure time string (e.g., "8:05 PM")
        price: Price string (e.g., "$634" or "634")
        origin: Origin airport code (e.g., "BOS") - for creating one-way search
        destination: Destination airport code (e.g., "ADB") - for creating one-way search
        date: Flight date in YYYY-MM-DD format - for creating one-way search

    Returns:
        Dict with flight_numbers (list) and connecting_segments (list of dicts), or None if not found.
        Example: {
            'flight_numbers': ['LH 423', 'XQ 505'],
            'connecting_segments': [
                {'airline': 'LH', 'flight_number': '423', 'from': 'BOS', 'to': 'MUC'},
                {'airline': 'XQ', 'flight_number': '505', 'from': 'MUC', 'to': 'ADB'}
            ]
        }
    """
    api_key = os.environ.get("BROWSERLESS_API_KEY")
    if not api_key:
        raise ValueError("BROWSERLESS_API_KEY environment variable is required")

    # If we have origin, destination, and date, create a one-way search URL
    # This is necessary for roundtrips because clicking an outbound flight
    # shows return options instead of outbound flight details
    if origin and destination and date:
        from fast_flights import create_filter
        from fast_flights.flights_impl import FlightData, Passengers

        oneway_filter = create_filter(
            flight_data=[FlightData(date=date, from_airport=origin, to_airport=destination)],
            trip="one-way",
            passengers=Passengers(adults=1),
            seat="economy"
        )
        url = "https://www.google.com/travel/flights?" + "&".join([
            f"tfs={oneway_filter.as_b64().decode('utf-8')}",
            "hl=en",
            "tfu=EgQIABABIgA",
            "curr="
        ])
    else:
        url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())

    # When using one-way search, prices will differ from roundtrip
    is_oneway_search = bool(origin and destination and date)
    return asyncio.run(_fetch_flight_details_async(url, api_key, airline, departure_time, price, origin, destination, is_oneway_search))


async def _fetch_flight_details_async(
    url: str, api_key: str, airline: str, departure_time: str, price: str,
    origin: str = "", destination: str = "", is_oneway_search: bool = False
) -> Optional[Dict]:
    """Async implementation of flight detail fetching.

    Note: For roundtrip searches, clicking an outbound flight shows return options,
    not outbound details. This function handles that by looking for flight numbers
    in the expanded view and using the origin/destination to determine direction.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            f"wss://production-sfo.browserless.io?token={api_key}"
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await page.add_init_script('delete Object.getPrototypeOf(navigator).webdriver')

        await page.goto(url)

        # Handle consent page
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
            await page.wait_for_timeout(2000)

        # Wait for flight results
        try:
            await page.wait_for_selector('li.pIav2d', timeout=30000)
        except Exception as e:
            await browser.close()
            return None

        await page.wait_for_timeout(5000)

        # Click "View more flights" buttons to ensure all flights are visible
        try:
            buttons = await page.locator('span.bEfgkb:has-text("View more flights")').all()
            for btn in buttons:
                try:
                    await btn.click()
                    await page.wait_for_timeout(2000)
                except:
                    pass
        except:
            pass

        # Normalize price for matching (remove $ and commas)
        price_clean = price.replace('$', '').replace(',', '').strip()

        # Find the flight row by matching airline, time, and price
        flight_items = await page.locator('li.pIav2d').all()

        target_item = None
        for item in flight_items:
            item_text = await item.inner_text()

            # Check if this item matches our flight
            # Match airline (check if any part of airline name is in the text)
            airline_parts = [a.strip() for a in airline.replace('+', ',').split(',')]
            airline_match = any(part.lower() in item_text.lower() for part in airline_parts)

            # Match departure time (normalize spaces)
            time_clean = departure_time.replace('\xa0', ' ').strip()
            time_match = time_clean in item_text.replace('\xa0', ' ')

            # Match price (skip for one-way searches since prices differ from roundtrip)
            if is_oneway_search:
                price_match = True  # Skip price matching for one-way
            else:
                price_match = price_clean in item_text.replace(',', '')

            if airline_match and time_match and price_match:
                target_item = item
                break

        if not target_item:
            await browser.close()
            return None

        # Scroll item into view and click to expand details
        try:
            await target_item.scroll_into_view_if_needed()
            await target_item.click()
            await page.wait_for_timeout(3000)

            # Capture the URL after clicking - Google may update it with selection info
            url_after_click = page.url
            if os.environ.get('DEBUG_FLIGHT_DETAILS'):
                print(f"DEBUG: URL after click: {url_after_click}")

            # Try to extract segments from Google's TFS in the URL
            google_segments = _extract_segments_from_google_tfs(url_after_click)
            if google_segments:
                await browser.close()
                return {
                    'flight_numbers': [f"{s['airline']} {s['flight_number']}" for s in google_segments],
                    'connecting_segments': google_segments
                }

        except Exception as e:
            await browser.close()
            return None

        # After clicking, the element may have changed. Get the full page content
        # which should now include the expanded flight details
        try:
            page_html = await page.inner_html('body')
            page_text = await page.inner_text('body')
        except Exception as e:
            await browser.close()
            return None

        # Use page content for extraction
        item_html = page_html
        item_text = page_text

        # Extract all airport codes found in the text (3-letter codes)
        all_airport_codes = re.findall(r'\b([A-Z]{3})\b', item_text)

        # Extract all route segments using multiple patterns
        all_routes = []

        # Pattern 1: BOS → IST or BOS–IST or BOS - IST
        routes_pattern1 = re.findall(r'([A-Z]{3})\s*[→–\-−]\s*([A-Z]{3})', item_html)
        all_routes.extend(routes_pattern1)

        # Pattern 2: Look for consecutive airport codes in text (e.g., "BOS ... IST")
        # This is a fallback when arrows aren't in the HTML
        if not all_routes and origin and destination:
            # Build routes from airport codes found, starting from origin
            valid_airports = []
            found_origin = False
            for code in all_airport_codes:
                if code == origin:
                    found_origin = True
                if found_origin:
                    if code not in valid_airports:  # Avoid duplicates
                        valid_airports.append(code)
                    if code == destination:
                        break

            # Create route pairs from consecutive airports
            for i in range(len(valid_airports) - 1):
                all_routes.append((valid_airports[i], valid_airports[i + 1]))

        # Extract all flight numbers (pattern: XX 1234 where XX is airline code)
        # Also try XX1234 format (no space)
        all_flights = re.findall(r'\b([A-Z]{2})[\s\.\-]?(\d{1,4})\b', item_html)

        # Filter to only include segments in the correct direction (origin → destination)
        # For roundtrips, Google shows both directions; we want segments starting from origin
        outbound_routes = []
        if origin and destination and all_routes:
            # Find segments that belong to the outbound direction
            # The first segment should start with origin, last should end with destination
            in_outbound = False
            for from_apt, to_apt in all_routes:
                if from_apt == origin:
                    in_outbound = True
                if in_outbound:
                    outbound_routes.append((from_apt, to_apt))
                if to_apt == destination:
                    break
        else:
            # No origin/destination provided, use all routes
            outbound_routes = all_routes

        # Deduplicate routes while preserving order
        seen_routes = set()
        unique_routes = []
        for route in outbound_routes:
            if route not in seen_routes:
                seen_routes.add(route)
                unique_routes.append(route)

        # Now extract unique flight numbers, filtering false positives
        seen_flights = set()
        flight_numbers = []

        for airline_code, flight_num in all_flights:
            # Skip common false positives (time indicators, units)
            if airline_code in ['AM', 'PM', 'CO', 'HR', 'KG', 'MI', 'GB', 'MB', 'KB']:
                continue

            flight_str = f"{airline_code} {flight_num}"
            if flight_str not in seen_flights:
                seen_flights.add(flight_str)
                flight_numbers.append(flight_str)

        # For roundtrips, the HTML shows both directions' flight numbers
        # The outbound flights appear first, then return flights
        # If we have routes, take only as many flight numbers as we have route segments
        if unique_routes and len(flight_numbers) > len(unique_routes):
            # For roundtrip, flight numbers are usually: [outbound1, outbound2, ..., return1, return2, ...]
            # Take only the first N where N = number of outbound segments
            flight_numbers = flight_numbers[:len(unique_routes)]

        # Build connecting_segments by pairing flight numbers with routes
        connecting_segments = []
        for i, flight_str in enumerate(flight_numbers):
            parts = flight_str.split()
            segment = {
                'airline': parts[0],
                'flight_number': parts[1] if len(parts) > 1 else ''
            }
            if i < len(unique_routes):
                segment['from'] = unique_routes[i][0]
                segment['to'] = unique_routes[i][1]
            else:
                # No route info available, leave empty
                segment['from'] = ''
                segment['to'] = ''
            connecting_segments.append(segment)

        # Final validation: if we have origin/destination, ensure segments form a valid path
        if origin and destination and connecting_segments:
            # Check if the segments form a valid outbound path
            valid_path = False
            if connecting_segments[0].get('from') == origin:
                # Check if path ends at destination
                last_to = connecting_segments[-1].get('to', '')
                if last_to == destination:
                    valid_path = True

            if not valid_path and len(connecting_segments) > 1:
                # Might have grabbed return flights instead - try reversing logic
                # This shouldn't happen if our extraction is correct, but as a safeguard
                pass

        await browser.close()

        if flight_numbers:
            return {
                'flight_numbers': flight_numbers,
                'connecting_segments': connecting_segments
            }
        return None


def browserless_fetch(params: dict) -> Any:
    """Fetch Google Flights data using Browserless.io Playwright service.

    Requires BROWSERLESS_API_KEY environment variable.
    """
    api_key = os.environ.get("BROWSERLESS_API_KEY")
    if not api_key:
        raise ValueError("BROWSERLESS_API_KEY environment variable is required")

    # Construct Google Flights URL
    url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())

    body = asyncio.run(_fetch_with_browserless(url, api_key))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse


async def _fetch_with_browserless(url: str, api_key: str) -> str:
    """Connect to Browserless.io via Playwright and fetch the page."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # Connect to Browserless.io via CDP
        browser = await p.chromium.connect_over_cdp(
            f"wss://production-sfo.browserless.io?token={api_key}"
        )

        # Create context with anti-detection measures
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # Remove webdriver property to avoid detection
        await page.add_init_script('delete Object.getPrototypeOf(navigator).webdriver')

        await page.goto(url)

        # Handle consent page if redirected
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
            await page.wait_for_timeout(2000)

        # Wait for flight results (try multiple selectors)
        try:
            await page.wait_for_selector('.eQ35Ce', timeout=30000)
        except Exception as e1:
            # Try waiting for any flight list item instead
            try:
                await page.wait_for_selector('li.pIav2d', timeout=10000)
            except Exception as e2:
                # Check if page shows "No results" - return HTML anyway for caller to handle
                pass

        # Wait for page to fully load (lazy loading)
        await page.wait_for_timeout(5000)

        # Click ALL "View more flights" buttons (there can be multiple in Best + Cheapest sections)
        try:
            buttons = await page.locator('span.bEfgkb:has-text("View more flights")').all()
            for btn in buttons:
                try:
                    await btn.click()
                    await page.wait_for_timeout(2000)
                except:
                    pass  # Button may have become stale, continue
        except:
            pass  # No buttons found, continue

        # Extract full page HTML including script tags (needed for JS parser to get flight numbers)
        body = await page.evaluate('() => document.documentElement.outerHTML')

        await browser.close()

    return body
