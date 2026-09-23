# BYS360 Devir ve Operasyon Dokümanları — Index

```
CURRENT CANONICAL HANDOVER:
BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md

Production SHA:
cb2e57c5d1829ea743c696ae78595a20755f3f07
```

Bu klasör, BYS360 projesinin kurulum, canlıya alma, bakım, güvenlik, modül envanteri ve süreklilik planı dokümanlarını içerir.

## Okuma Sırası (Yeni Operatör İçin)

1. **`BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md`** — tek kanonik, güncel devir belgesi (single source of truth). Tüm mimari, deployment, DB, backup, CI, güvenlik, Scheduled Task, rollback, disaster-recovery bilgisi burada tek dosyada toplanmıştır (34 bölüm, Dosya Merkezi §34 dahil).
2. **`BYS360_FEATURE_COVERAGE_MATRIX.md`** — repo-türetilmiş TAM özellik envanteri (38 feature) ve her birinin gerçek devir-kapsam durumu (DOCUMENTED/PARTIAL/UNDOCUMENTED/HISTORICAL/FUTURE). "Bu özellik handover'da unutuldu mu?" sorusunun kanıtlı cevabı için buraya bakın.
3. Kök dizindeki `DEPLOYMENT.md` ve `BACKUP_RUNBOOK.md` — kanonik ana dosyanın dayandığı, güncel (Ağustos 2026) operasyonel runbook'lar.
4. Kök dizindeki `README.md`, `CONTRIBUTING.md`, `SECURITY.md` — genel bakış ve katkı kuralları.

Aşağıdaki listedeki diğer dosyalar **SUPERSEDED** veya **HISTORICAL**'dir (silinmemiştir, ama artık kanonik kaynak değildir — ayrıntılı gerekçe için kanonik dosyanın §33 "Eski Belgeler" bölümüne bakın):

| Belge | Durum | Tarih |
|---|---|---|
| `BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` | **CURRENT** | 2026-08-24 |
| `BYS360_FEATURE_COVERAGE_MATRIX.md` | **CURRENT** (companion) | 2026-08-24 |
| `BYS360_DEVIR_PAKETI_V1.md` | SUPERSEDED | 2026-06-24 |
| `BYS360_KURULUM_REHBERI.md` | SUPERSEDED | 2026-06-24 |
| `BYS360_CANLIYA_ALMA_REHBERI.md` | SUPERSEDED | 2026-06-24 |
| `BYS360_BAKIM_RUNBOOK.md` | SUPERSEDED | 2026-06-24 |
| `BYS360_GUVENLIK_KVKK_NOTLARI.md` | SUPERSEDED | 2026-06-24 |
| `BYS360_MODUL_ENVANTERI.md` | SUPERSEDED | 2026-06-24 |
| `BYS360_RISK_VE_SUREKLILIK_PLANI.md` | SUPERSEDED | 2026-06-24 |
| `HANDOVER_10_10_EVIDENCE_20260708.md` | HISTORICAL | 2026-07-08 |

## Temiz Kaynak Noktası (Tarihsel)

- Temizlik etiketi: `local-clean-ai-traces-complete-20260624`
- Devir doküman dalı: `handover-docs-v1`
- Bu etiket/dal referansı bu index güncellemesi sırasında repo içinde bağımsız olarak yeniden doğrulanmamıştır — güncel devir için `BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md`'nin baş kısmındaki `Production Source SHA` kanonik referanstır.

## Devir Notu

Bu dokümanlar, kaynak kodun yanında teslim edilmesi gereken operasyonel bilgi setidir. Gerçek parola, token, gizli anahtar, veritabanı şifresi veya kişisel veri içermez.
