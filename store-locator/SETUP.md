# Paulie's Store Locator: Setup (about 15 min)

Map now reads from the **Current Accounts** tab, not ORDERS.

## 1. Add the geocoder (once)
1. Open "Paulie's Order Form (Responses)" > Extensions > Apps Script.
2. Paste `geocode.gs`, click Save. Close the tab.

## 2. Add a public "Store Locator" tab
Keeps contacts, emails, and license numbers private. Only this tab gets published.
1. Add a new tab named `Store Locator`.
2. A1: `=QUERY('Current Accounts'!A3:D, "select A, B, C, D where A is not null and D is not null", 1)`
3. E1: `Lat`   F1: `Lng`
4. E2: `=GEOCODE(D2:D200)` (approve the permission prompt the first time)
5. Spot-check: any row showing NOT FOUND needs its address fixed in Current Accounts.

## 3. Publish just that tab
File > Share > Publish to web > pick `Store Locator` (not "Entire document") > CSV > Publish.
Make sure "Automatically republish when changes are made" is checked. Copy the URL.

## 4. Install in Shopify
1. Online Store > Themes > ... > Edit code > Sections > Add a new section > `paulies-store-locator`.
2. Replace its contents with `paulies-store-locator.liquid`. Save.
3. Customize > go to the Store Locator page > remove the old locator section/app block > Add section > "Paulie's store locator".
4. Paste the CSV URL into the section setting. Set accent color. Save.

## Ongoing
- New account? Add a row in Current Accounts. It shows on the site within ~5 min.
- Remove a store: delete its row (or move it off the tab).
