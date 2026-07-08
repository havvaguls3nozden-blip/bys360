# ADR-0001 — Opsiyonel Başlangıç Bileşenlerinde Sessiz Hata Yutma Kaldırıldı

## Durum
Kabul edildi.

## Bağlam
BYS360 uygulama başlangıcında bazı opsiyonel bileşenler uygulamanın açılışını engellememek için `try/except/pass` ile sarılmıştı. Bu yaklaşım canlıda kesinti riskini azaltır; ancak hatayı tamamen gizlediği için PWA, mobil API, HR shim veya asistan görünürlüğü gibi bileşenlerin kayıtsız kalmasına sebep olabilir.

## Karar
Opsiyonel bileşen davranışı korunur: hata uygulama açılışını engellemez. Ancak hata artık `app.logger.exception(...)` ile stack trace içerecek şekilde loglanır.

## Sonuç
- Canlı açılış dayanıklılığı korunur.
- Gizli başlangıç arızaları görünür hale gelir.
- 10/10 kalite hedefindeki gözlemlenebilirlik şartı güçlenir.
