# BYS360 P4B V3 Mobile Role Boundary Matrix Gate

Bu hotfix, P4B V2 runtime route map kontrolünde dinamik Flask parametrelerinin (`<int:id>` gibi) numerik test pathleriyle eşleşmemesi nedeniyle oluşan yanlış negatifleri düzeltir.

## Kapsam

- Mobil route sözleşmesi: `app/api/mobile/routes.py` facade olarak kalır, route decorator domain dosyalarında korunur.
- Runtime route map: `app.url_map` doğrudan okunur. Dinamik Flask converter parçaları regex ile doğru eşleştirilir.
- Role boundary matrix: sahte admin/personel bearer token, rol header taklidi, malformed token ve yetkisiz isteklerde açık 2xx, 404/405 veya 5xx oluşmaması beklenir.
- Canlı veriye yazmaz; test client üzerinden güvenli smoke yapar.

## Beklenen sonuç

```json
{
  "ok": true,
  "runtime_route_map_ok": true,
  "role_boundary_matrix_ok": true
}
```
