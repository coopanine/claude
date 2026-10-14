/**
 * Paulie's store locator geocoder.
 * Paste into Extensions > Apps Script on "Paulie's Order Form (Responses)", then save.
 *
 * Usage in a cell: =GEOCODE(D2:D200)  -> fills two columns: Lat, Lng
 *
 * @param {string|Array} input An address, or a column of addresses.
 * @return Lat and Lng for each address.
 * @customfunction
 */
function GEOCODE(input) {
  var cache = CacheService.getScriptCache();

  function one(addr) {
    addr = String(addr || '').trim();
    if (!addr) return ['', ''];
    var key = 'geo:' + Utilities.base64Encode(
      Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, addr));
    var hit = cache.get(key);
    if (hit) return JSON.parse(hit);
    var res = Maps.newGeocoder().setRegion('us').geocode(addr);
    if (res.status !== 'OK' || !res.results.length) return ['NOT FOUND', ''];
    var loc = res.results[0].geometry.location;
    var out = [loc.lat, loc.lng];
    cache.put(key, JSON.stringify(out), 21600); // 6 hours (max)
    return out;
  }

  if (Array.isArray(input)) return input.map(function (row) { return one(row[0]); });
  return [one(input)];
}
