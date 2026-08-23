import requests

TFL_BASE = "https://api.tfl.gov.uk"
TIMEOUT = 10

# Tube station NaPTAN ids start with this; hub ids (HUBWAT etc.) do not.
# Confirms a result IS a tube station. Cannot confirm it is the RIGHT one --
# Brent Cross passes this check.
TUBE_ID_PREFIX = "940GZZLU"

# A list, not a set: output order must be stable so it can be reviewed and
# compared between runs.
STATIONS = [
    "Waterloo",
    "Liverpool Street",
    "Tottenham Court Road",
    "Bond Street",
    "Bank",
    "Oxford Circus",
    "Victoria",
    "London Bridge",
    "Vauxhall",
    "Leicester Square",
]


def get_json(url, params=None):
    """Make one GET. Return (ok, payload_or_error_string). Never raises."""
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return False, f"request failed: {exc}"

    if response.status_code != 200:
        return False, f"HTTP {response.status_code}"

    try:
        return True, response.json()
    except ValueError:
        return False, "response was not JSON"


def search_station(name):
    """Return the list of candidate matches for a station name.

    None  -> the request itself failed
    []    -> the request worked, nothing matched
    """
    ok, payload = get_json(f"{TFL_BASE}/StopPoint/Search/{name}",
                           params={"modes": "tube"})
    if not ok:
        return None
    return payload.get("matches", [])


def check_crowding(naptan):
    """Return (data_available, percentage_or_None).

    (None, None)  -> the request failed
    (False, None) -> TfL answered; no live feed for this station
    (True, 0.31)  -> a real reading

    dataAvailable:false arrives with percentageOfBaseline:0. That zero is a
    null, not a measurement -- never return it as a number.
    """
    ok, payload = get_json(f"{TFL_BASE}/crowding/{naptan}/Live")
    if not ok:
        return None, None

    if not payload.get("dataAvailable"):
        return False, None

    return True, payload.get("percentageOfBaseline")


def names_agree(requested, matched):
    """Does the matched name plausibly correspond to what was asked for?

    Passes:
        ("Oxford Circus", "Oxford Circus Underground Station") -> True
        ("Waterloo",      "Waterloo")                          -> True
        ("TCR",           "Brent Cross Underground Station")   -> False

    Substring, not equality: TfL is inconsistent about the "Underground
    Station" suffix, so == would flag Oxford Circus as a mismatch.

    What this gets wrong -- it is a flag for human review, not a validator:
      - FALSE POSITIVE on short names that are substrings of other stations.
        "Bank" is contained in "Embankment Underground Station".
      - FALSE NEGATIVE on punctuation. "Kings Cross" is not a substring of
        "King's Cross St. Pancras Underground Station" (apostrophe).
    """
    return requested.strip().lower() in matched.lower()


def describe_crowding(available, pct):
    """Format check_crowding()'s two return values for display.

    Display only. main() branches on `available` itself, never on this
    string, so changing the wording here cannot change any decision.

    `is None` / `is False` rather than `if not available`: both are falsy but
    they are different facts, and collapsing them is the same mistake as
    letting dataAvailable:false arrive as 0.
    """
    if available is None:
        return "request failed"
    if available is False:
        return "no data"
    if pct is None:
        return "no value"
    return f"{pct:.2f}"


def main():
    confirmed = {}
    needs_review = []

    for name in STATIONS:
        print(f"\n{name}")

        candidates = search_station(name)

        if candidates is None:
            print("    search request failed")
            needs_review.append((name, "search request failed"))
            continue

        if not candidates:
            print("    no matches")
            needs_review.append((name, "no matches - check the spelling"))
            continue

        # NOTE: `problems` accumulates across ALL candidates for this station,
        # so one bad candidate blocks a good one at the same station from
        # being auto-confirmed. Deliberate: any ambiguity gets human review.
        problems = []
        if len(candidates) > 1:
            problems.append(f"{len(candidates)} candidates")

        for match in candidates:
            naptan = match["id"]
            matched_name = match["name"]

            agrees = names_agree(name, matched_name)
            is_tube = naptan.startswith(TUBE_ID_PREFIX)

            if is_tube:
                available, pct = check_crowding(naptan)
            else:
                available, pct = None, None

            crowding = describe_crowding(available, pct) if is_tube else "-"

            flag = "ok   " if (agrees and is_tube) else "CHECK"
            print(f"    {flag} {naptan:<14} {matched_name:<42} {crowding}")

            if not agrees:
                print(f'          ^ "{name}" does not appear in that name')
                problems.append(f"name mismatch: {matched_name}")
            elif not is_tube:
                print("          ^ not a station id - crowding won't work")
                problems.append(f"hub id: {naptan}")
            elif available is None:
                problems.append("crowding request failed")
            elif available is False:
                problems.append("no live crowding")
            elif not problems:
                confirmed[naptan] = matched_name

        if problems:
            needs_review.append((name, "; ".join(problems)))

    print()
    print("=" * 72)
    print(f"CONFIRMED ({len(confirmed)}) - safe to paste into collect.py")
    print("=" * 72)
    print("STATIONS = {")
    for naptan, matched_name in confirmed.items():
        print(f'    "{naptan}": "{matched_name}",')
    print("}")

    if needs_review:
        print()
        print("=" * 72)
        print(f"NEEDS YOUR EYES ({len(needs_review)}) - deliberately excluded above")
        print("=" * 72)
        for name, reason in needs_review:
            print(f"    {name:<26} {reason}")


if __name__ == "__main__":
    main()
