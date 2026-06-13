# BYS360 S0E Reports/Quality Backup Archive Cleanup

Tarih: 2026-06-13T10:06:14

## Sonuç

- OK: True
- Karar: S0E_GREEN
- Archive root: `C:\bys360\releases\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448`
- Restore script: `C:\bys360\releases\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\RESTORE_S0E_REPORTS_QUALITY_BACKUPS.ps1`
- Candidate count: 17
- Operation count: 17
- Error count: 0
- Backup test dir count after: 0
- Quality backup dir count after: 0
- Backup collection hit count: 0
- Compileall returncode: 0
- Collect-only returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0
- Pytest default returncode: 0

## Operations

```json
[
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p1_archive_marker_safe_v1_backups_20260612_090923",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p1_archive_marker_safe_v1_backups_20260612_090923",
    "before": {
      "source": "reports/quality/a5_p1_archive_marker_safe_v1_backups_20260612_090923",
      "file_count": 82,
      "test_file_count": 82,
      "size_bytes": 145267,
      "size_mb": 0.139,
      "files_top_300": [
        {
          "relative_path": "tests/architecture/test_android_responsive_baseline_p5a.py",
          "size_bytes": 956,
          "sha256": "897e7089763e89f7cd83e04e47531e2da3080fbfbb56ca75e577a5802aa8de40"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_final_evidence_p5f.py",
          "size_bytes": 590,
          "sha256": "59324eae94a2e4422049db06c1b6eb6f5d8dc7e70e127acb1643dcc7f8e7c71d"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_inventory_precision_p6c.py",
          "size_bytes": 696,
          "sha256": "c5a8ac6772d2d14dd5db211e0c94d9ba08c82819cfcd222ba5435557f6108940"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_release_suite_p5d_v2.py",
          "size_bytes": 550,
          "sha256": "f82b92d015e8ba5b4e03dcafca510ba6bed5cb05d8c022e19b3f6653a3fedff7"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_visual_regression_p6a.py",
          "size_bytes": 791,
          "sha256": "214ac5df7cf0b806105560c3fa87ed42f8ca0059a76d493034d74308874b08b3"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_visual_uat_evidence_p5e.py",
          "size_bytes": 559,
          "sha256": "1724dee8430fc0b7313e45254bd532955f6118ea60fd6f2b4259ae58a190cf11"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz10_contract.py",
          "size_bytes": 2168,
          "sha256": "28a4f7f5daaba1848edd8dcdff214c0aa27da0a2a9a97be8626a4834776fb97c"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz2_contract.py",
          "size_bytes": 735,
          "sha256": "661b1d27f3ed05973df16d990fb01b9d4f8548457d9c3d1fcb79d3850cc06670"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz5_contract.py",
          "size_bytes": 2393,
          "sha256": "917148fae177295c25e0c6417fbb0bb14eb7e7e9a6f61df80adf7303087fd862"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz6_contract.py",
          "size_bytes": 1608,
          "sha256": "7653c06e3355fe6015da24d7d4becfd50b4c8fce3f5ceb48649266d7230547bc"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz7_contract.py",
          "size_bytes": 1681,
          "sha256": "97df77067683750e6d1f0b83670d53d3773bc772a75d0c9e20db96c4e8c85f09"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz8_contract.py",
          "size_bytes": 2171,
          "sha256": "0f56b90c118b50202936818282502ca2cb185f4d90ba5e988caf9aa300383ab1"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz9_contract.py",
          "size_bytes": 2140,
          "sha256": "4413808396bf047189a11a9d8a0a222b443c4a0f0b555c160903d08ae766513a"
        },
        {
          "relative_path": "tests/architecture/test_home_phase1_contract.py",
          "size_bytes": 1759,
          "sha256": "9adf99d4ed9f34c44dddbe3f61645662720c535eb576773de103a3b7ff135810"
        },
        {
          "relative_path": "tests/architecture/test_message_faz1_smoke_contract.py",
          "size_bytes": 6087,
          "sha256": "be3333e0e40be379f3dbfe079a401aa4131420d2e0b4fe21d6b98c6b260f00b0"
        },
        {
          "relative_path": "tests/architecture/test_message_faz2_service_contract.py",
          "size_bytes": 2304,
          "sha256": "a42ee87a19056f9552a7ebf6d9f7cf0ab39650e6b2d8477fea2bcecc98823c57"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_release_evidence_p4e.py",
          "size_bytes": 933,
          "sha256": "27256f7aac81b9ebe6cb534ba584a665b5c51f67a258531da616d80d113ae300"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_request_smoke_p2c.py",
          "size_bytes": 748,
          "sha256": "bcd0fe10dae23f8ed184547f4f3cccf5a2820bab128ca0a5cea1652c9610e398"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_role_boundary_matrix_p4b.py",
          "size_bytes": 644,
          "sha256": "b46fe815bcf0a13713b32373eebe114b0ee8c56c798ede4239fee1fb8ae83ecc"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v2.py",
          "size_bytes": 650,
          "sha256": "e97a881eb7c1e5d448956d0403636630fe90326d6474bd94930d7f0df00d81d1"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_security_evidence_p4d.py",
          "size_bytes": 1377,
          "sha256": "21fa58f8949fd9657b5f5cdd2488e1bd7adebc80a80f12c8efaeef56da3ca76d"
        },
        {
          "relative_path": "tests/architecture/test_portal_service_faz6_contract.py",
          "size_bytes": 2726,
          "sha256": "a4abc0f1303109f75a6a62739b193ff472268a264478b81db87a9dac3ccd4bbd"
        },
        {
          "relative_path": "tests/architecture/test_settings_faz0_live_contract.py",
          "size_bytes": 2321,
          "sha256": "41850f5308d983c8701dbf5ab4aac89e0305500dd0f9f0209ce176e8b74111c1"
        },
        {
          "relative_path": "tests/architecture/test_settings_faz2_service_bridge.py",
          "size_bytes": 1924,
          "sha256": "89f298bb219bb9993458eca7053d387af4b056cb4f33312716edf6e3c48b4fe4"
        },
        {
          "relative_path": "tests/architecture/test_settings_faz3_snapshot_contract.py",
          "size_bytes": 1397,
          "sha256": "2f3305428acf4b1426fdd5e2ab85c5d033c5ee99591eb98f463df9b04c69c1dd"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz1_smoke_contract.py",
          "size_bytes": 5920,
          "sha256": "d4e470ab8bd44e0b65d4e2c3d763fbd29d4a416dbaf4c0bd2ff9d03890de27c7"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz2_service_contract.py",
          "size_bytes": 1948,
          "sha256": "736bc3c32ddc996ea50e432884af9269b34eb185c549c240a057263ece3553df"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz3_route_service_bridge.py",
          "size_bytes": 2455,
          "sha256": "5ce887308d5ef560c9e934401409ad8ed0e9296b4bd614695461c614a489cfd5"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz4_read_service_contract.py",
          "size_bytes": 1846,
          "sha256": "09621d0731964f070adb922344be66e89f84f8d32487a7ba8896f975a4191f04"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz6_target_access_contract.py",
          "size_bytes": 1544,
          "sha256": "2fea0e3b95e5825e22db399cda7ecb50029762740c280470581169dffbfcde4a"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz7_submit_contract.py",
          "size_bytes": 2290,
          "sha256": "bb9280714122a2f0d2d65c52bc9a2f82e735f885f10398afa67520dc7351b306"
        },
        {
          "relative_path": "tests/architecture/test_survey_live_contract.py",
          "size_bytes": 1488,
          "sha256": "ed79318134f59a768981c7a2e78d71a4e6c02341cfa139af43a293fb05c0bb13"
        },
        {
          "relative_path": "tests/communication/test_communication_template_presence.py",
          "size_bytes": 1036,
          "sha256": "9193dc55c086a964959dc0b456968ae0bd67821a480eecd77a2cd667fd7b3bbb"
        },
        {
          "relative_path": "tests/communication/test_phase9a_route_contracts.py",
          "size_bytes": 534,
          "sha256": "60888e9e883e0d3f9ee755ad298fec19a6175be321bb2e5cea44a53f26e8dec9"
        },
        {
          "relative_path": "tests/expert_review/test_phase10_expert_final_gate.py",
          "size_bytes": 1221,
          "sha256": "006a865477a2f581e2800b0c6d9574fe0e6bd7c9d79c54cfa57fb638ff8971a0"
        },
        {
          "relative_path": "tests/expert_review/test_phase13_final_expert_review_package.py",
          "size_bytes": 1011,
          "sha256": "92ea51f2871181544954c3de841b40be08166d440292edbf3268aa5d23405157"
        },
        {
          "relative_path": "tests/integration/test_final_quality_live_backbone_release_contract.py",
          "size_bytes": 2587,
          "sha256": "d12bf95a0a181fb5e041f8112891d2405148596f6a60804032fec9ef449d6d62"
        },
        {
          "relative_path": "tests/integration/test_sprint2_auth_login_smoke_v5.py",
          "size_bytes": 1196,
          "sha256": "4b49c04512d267f7598483dbcce7a2f6e61afd415a191e9e8205fcfead13d8ad"
        },
        {
          "relative_path": "tests/integration/test_sprint2_closure_freeze_v19.py",
          "size_bytes": 2206,
          "sha256": "9fefca0939ed5cab5b748ebc3867c6f1fa9675eeee5575273ccad23624bc1de5"
        },
        {
          "relative_path": "tests/integration/test_sprint2_closure_freeze_waiting_mode_hotfix_v19_1.py",
          "size_bytes": 2255,
          "sha256": "05a3369b82c54ff1d1e632a0d97675f38f810467a660d37154e7eea270abb9a7"
        },
        {
          "relative_path": "tests/integration/test_sprint2_critical_pages_smoke_v7.py",
          "size_bytes": 2023,
          "sha256": "2dd46468da071f2e5d28a77af46b061fe0a34baabc30113bb7261d8c329f4757"
        },
        {
          "relative_path": "tests/integration/test_sprint2_deployment_runbook_rollback_v16.py",
          "size_bytes": 2070,
          "sha256": "31c7f3d5f2a07a528c0b4f2a454acec8ef5f7b0e378ed55753c28926d072ae31"
        },
        {
          "relative_path": "tests/integration/test_sprint2_final_regression_matrix_v9.py",
          "size_bytes": 1953,
          "sha256": "7c1ae78891c2f80000712cd08be27b2c2905a36b81e2c6aa0d94af260d5b590e"
        },
        {
          "relative_path": "tests/integration/test_sprint2_integration_smoke_v4.py",
          "size_bytes": 2223,
          "sha256": "44b4b301c9dee6d25fea8fe17af5791bf867c74dac8ecd02ad1d61eb923c2b22"
        },
        {
          "relative_path": "tests/integration/test_sprint2_legacy_integration_scope_v8.py",
          "size_bytes": 2002,
          "sha256": "031f1926d0dc562aebfdf3d961f106d8aabc8a4b2188e572b6774a3b9451aeb7"
        },
        {
          "relative_path": "tests/integration/test_sprint2_live_server_preflight_v17.py",
          "size_bytes": 2441,
          "sha256": "5659a9eb769bb24c6739f38cd6562773946fffaa6ab85e0372d9b2ed7f00378b"
        },
        {
          "relative_path": "tests/integration/test_sprint2_real_login_smoke_v6.py",
          "size_bytes": 1835,
          "sha256": "4e709fb5e6dc22c2a5495f0f20cd08a801aa2f562c04bb929954d8c92cfb8d5d"
        },
        {
          "relative_path": "tests/integration/test_sprint2_release_candidate_verify_v13.py",
          "size_bytes": 1703,
          "sha256": "98afd84fc60e962abc6496fcd150f4ed03386381f43756cef9508421abcd949d"
        },
        {
          "relative_path": "tests/integration/test_sprint2_release_evidence_bundle_v14.py",
          "size_bytes": 1785,
          "sha256": "789dae33af157d303a16bfe40561e11219967af399c09a7544ee82706c7b16ba"
        },
        {
          "relative_path": "tests/integration/test_sprint2_release_manifest_dry_run_v11.py",
          "size_bytes": 1777,
          "sha256": "c398354be7bf8bcff1c7be6d00f41f5c3cbf1b0faa5f7f7cbc8c50bb3246b77a"
        },
        {
          "relative_path": "tests/integration/test_sprint2_release_package_builder_v12.py",
          "size_bytes": 1575,
          "sha256": "d8aed466b573b2e12a7ff03d8e5f455711f435651d9c6540ee0035c4fd4eb654"
        },
        {
          "relative_path": "tests/integration/test_sprint2_release_readiness_v10.py",
          "size_bytes": 2098,
          "sha256": "c72cc6d1342d96244ff910918d9ad7f381ccc942a4ab3192bb087d5fe08e640d"
        },
        {
          "relative_path": "tests/integration/test_sprint3_closure_freeze_next_stage_phrase_hotfix_v6_1.py",
          "size_bytes": 1081,
          "sha256": "33de5196191525708ed7dd3ba4552b9b733929dd33bc537825e45c5b4a127db4"
        },
        {
          "relative_path": "tests/integration/test_sprint3_closure_pilot_acceptance_freeze_v6.py",
          "size_bytes": 2285,
          "sha256": "015f091dbd2f4641cfb1ab81ce41a108dfe893af09b43e3d14195b0b5acc6132"
        },
        {
          "relative_path": "tests/integration/test_sprint3_corporate_approval_decision_consolidation_v5.py",
          "size_bytes": 2261,
          "sha256": "67379f62b922a66fc168adf7e6e16ebaad2d308f089456889a7a9f59d8135fdf"
        },
        {
          "relative_path": "tests/integration/test_sprint3_corporate_approval_minutes_live_note_hotfix_v4_1.py",
          "size_bytes": 1417,
          "sha256": "53975fe0d6af9bb92ccb7501ec510e66bc62512a2abbde7f17bb6e1af61624d2"
        },
        {
          "relative_path": "tests/integration/test_sprint3_corporate_approval_pack_v4.py",
          "size_bytes": 2113,
          "sha256": "724118cd8ec9a90fb76db4fd0102bedd699274ae00c5da60d632ca0ace45549c"
        },
        {
          "relative_path": "tests/integration/test_sprint3_pilot_execution_matrix_v2.py",
          "size_bytes": 2558,
          "sha256": "7977ffc1ef3d29547ab7c7833be69d6ab25b954d78409072553b92cb20e646a7"
        },
        {
          "relative_path": "tests/integration/test_sprint3_pilot_triage_board_v3.py",
          "size_bytes": 2297,
          "sha256": "a8e794e9ff6021bda6ac01e174d5e8ecd1c2d2914075c4220b06af06caf2dc99"
        },
        {
          "relative_path": "tests/integration/test_sprint3_uat_pilot_plan_v1.py",
          "size_bytes": 2465,
          "sha256": "2751e6a803afc7f6a6e9c26ff6e06009e18d9fc5e8c296208686c0c6e583fde4"
        },
        {
          "relative_path": "tests/ops/test_live_ops_contract.py",
          "size_bytes": 1389,
          "sha256": "6dbacc6a4ee62707afa87881530e1b1950c41178d3e703fd26245a1004983fed"
        },
        {
          "relative_path": "tests/release/test_final_quality_release_chain_contract.py",
          "size_bytes": 2688,
          "sha256": "95992ca946963b98f599112f9d512ee51d9f043cfc12142737f9ef397f6b409a"
        },
        {
          "relative_path": "tests/release/test_final_quality_release_report_contract.py",
          "size_bytes": 1447,
          "sha256": "435dd9c61769ef6aec3044d93948509320832775819f537c1e26494bedfa4a64"
        },
        {
          "relative_path": "tests/release/test_phase11_release_clean_gate.py",
          "size_bytes": 939,
          "sha256": "877091297e841427163774a2ad26fe224dfd1ca8aa08fb2f273165d69905bf61"
        },
        {
          "relative_path": "tests/security/test_final_quality_security_release_contract.py",
          "size_bytes": 2134,
          "sha256": "18323a361a05f7af51882b4c55f5459cf6b932755d916282473f05d83df891fc"
        },
        {
          "relative_path": "tests/services/test_final_quality_home_weather_contract.py",
          "size_bytes": 1798,
          "sha256": "d14ce913cdc564ea698a258bf767cb7af9cbbe6f9c2004577d1a5debeee7c2b9"
        },
        {
          "relative_path": "tests/services/test_final_quality_live_source_contract.py",
          "size_bytes": 2478,
          "sha256": "35e7ece10d7b78f901658612ebc6419c5a1d138708efb5eca4afacaf6d6858a4"
        },
        {
          "relative_path": "tests/sprint2/test_sprint2_coverage_baseline_v3.py",
          "size_bytes": 892,
          "sha256": "b67aa95cf63e9f293ef4ad82001dd7b057c00b3fa5cc8c7d5a2756ee12afee69"
        },
        {
          "relative_path": "tests/sprint2/test_sprint2_critical_guard_tests_v2.py",
          "size_bytes": 2522,
          "sha256": "44e1dd8d3ee6ae0683e2e8e9a34d03bd59c0bb2235515e379ec7b7912c1402b7"
        },
        {
          "relative_path": "tests/sprint2/test_sprint2_test_infra_v1.py",
          "size_bytes": 1176,
          "sha256": "5898f6a03829be16f24f81dee3f2192f043c5328d9865eead63b23839bb7cf46"
        },
        {
          "relative_path": "tests/test_ai_analysis_visual_reports_static.py",
          "size_bytes": 1067,
          "sha256": "9591d9751da8393dad81bf90cf2363be8cd5a78f97386d0daef800c62999d84a"
        },
        {
          "relative_path": "tests/test_ai_final_live_hardening_static.py",
          "size_bytes": 1332,
          "sha256": "5f0dcda2a06fc38c9945e90ba7762bf3b21a78c454b7a5310768eccf46dafa0b"
        },
        {
          "relative_path": "tests/test_ai_visibility_gate_static.py",
          "size_bytes": 1492,
          "sha256": "1cee8c264cd90484cd4f770d18b48ff497a3f41cf93c9ffb8ffaf1469a30a583"
        },
        {
          "relative_path": "tests/test_async_task_infrastructure_static.py",
          "size_bytes": 1129,
          "sha256": "fcb4f745090e382a31ae1b35c251d8cd65291ce61d06831b02096a2f67329cbb"
        },
        {
          "relative_path": "tests/test_claude_phase5_smoke_routes.py",
          "size_bytes": 3290,
          "sha256": "c8299d3da56c8e6c6f0fa3c379c47183ed1502c68f9dd7f103d2e9312e3e54a8"
        },
        {
          "relative_path": "tests/test_hr_leave_attendance_real_post_static.py",
          "size_bytes": 1682,
          "sha256": "72b09fde2d7b581b6a614a08bc9490518d2289fb77cc29e58395d62cd8986d97"
        },
        {
          "relative_path": "tests/test_institutional_dashboard_route_static.py",
          "size_bytes": 1056,
          "sha256": "951bc24f1a5bcf48d6394fa175aefcd50ca9bd3b3e0b2113b77007bd11e36854"
        },
        {
          "relative_path": "tests/test_live_scope_and_security_static.py",
          "size_bytes": 1060,
          "sha256": "800e2951652aefd2b1d8c0a8a9f58cb07cfb93351dc8d4f226d7cf9c353ef106"
        },
        {
          "relative_path": "tests/test_performance_assignment_rule_gate_static.py",
          "size_bytes": 1603,
          "sha256": "176993b190fe7f003835afcdb48d95c844af6d99c7fa25a588886c861ab7247c"
        },
        {
          "relative_path": "tests/test_performance_core_health_dalga8_static.py",
          "size_bytes": 1991,
          "sha256": "2749de539aa7282e78b0437795d819945335336f41307708c81e73223be9306a"
        },
        {
          "relative_path": "tests/test_performance_phase5_ui_copy.py",
          "size_bytes": 1160,
          "sha256": "960d0c5d5a52037aa85bdf223e954387899dec231d282d7db0b580a0eee43855"
        },
        {
          "relative_path": "tests/test_performance_visibility_constitution_static.py",
          "size_bytes": 1535,
          "sha256": "dc0ab8b329f03b7691ae535e9f8dc7e4b52ebd316919274dff9515b8323522bb"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p1_archive_marker_safe_v1_backups_20260612_090923",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 82,
      "destination_test_file_count": 82,
      "destination_size_mb": 0.139
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2_manual_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2_manual_backups",
    "before": {
      "source": "reports/quality/a5_p2_manual_backups",
      "file_count": 3,
      "test_file_count": 3,
      "size_bytes": 2948,
      "size_mb": 0.003,
      "files_top_300": [
        {
          "relative_path": "test_docs_expert_review_contract.py",
          "size_bytes": 1201,
          "sha256": "f9744d4f964580ad5dda9ffbbfa420ef40e5b5ebc039cc501af973d35da03ba0"
        },
        {
          "relative_path": "test_redis_ready_static.py",
          "size_bytes": 933,
          "sha256": "f9f4c0fd516bba0404ca8316faea9d757e07b0c7ef53426f1e41127e996488b5"
        },
        {
          "relative_path": "test_sprint3_pilot_triage_board_test_syntax_hotfix_v3_1.py",
          "size_bytes": 814,
          "sha256": "161b0794f4e5c655fe9672507ac2c95e8b291ee4de638b302130d6103b4b4502"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2_manual_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 3,
      "destination_test_file_count": 3,
      "destination_size_mb": 0.003
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2c_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2c_backups",
    "before": {
      "source": "reports/quality/a5_p2c_backups",
      "file_count": 2,
      "test_file_count": 1,
      "size_bytes": 3483,
      "size_mb": 0.003,
      "files_top_300": [
        {
          "relative_path": "conftest_before_p2c.py",
          "size_bytes": 2920,
          "sha256": "d4e1d8fc0cc129247b2a4156e4b6db76d7fbc9840174b5db0bedec7824194b5f"
        },
        {
          "relative_path": "test_compat_redirects_before_isolation.py",
          "size_bytes": 563,
          "sha256": "a358a4482d070aa7a35fa565390386f29a06e293294ab13d515363539701eae6"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2c_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 2,
      "destination_test_file_count": 1,
      "destination_size_mb": 0.003
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d1_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d1_backups",
    "before": {
      "source": "reports/quality/a5_p2d1_backups",
      "file_count": 3,
      "test_file_count": 3,
      "size_bytes": 4154,
      "size_mb": 0.004,
      "files_top_300": [
        {
          "relative_path": "test_10_10_core_static_gate.py",
          "size_bytes": 2600,
          "sha256": "1ff395c6eece95dee42f0a9013598f6f12240a79cb9438e0cf33c4fbd51979e8"
        },
        {
          "relative_path": "test_module_maturity_scoring.py",
          "size_bytes": 784,
          "sha256": "ecb3747e5e73194827c64085c8af5709fb789003733372917861543fd8f4a378"
        },
        {
          "relative_path": "test_performance_preflight.py",
          "size_bytes": 770,
          "sha256": "ffd5f0607f7b9a784f03f4c8a3289efc5b06b30c893c0da3def10f1aca76b92e"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d1_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 3,
      "destination_test_file_count": 3,
      "destination_size_mb": 0.004
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d2_feedback_pulse_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d2_feedback_pulse_backups",
    "before": {
      "source": "reports/quality/a5_p2d2_feedback_pulse_backups",
      "file_count": 2,
      "test_file_count": 0,
      "size_bytes": 244883,
      "size_mb": 0.234,
      "files_top_300": [
        {
          "relative_path": "base.html",
          "size_bytes": 118139,
          "sha256": "50c5ec6643e175c43e4ffcc4b67537fd7ade567677a78b4d654bd5e08b5e24a5"
        },
        {
          "relative_path": "menu_registry.py",
          "size_bytes": 126744,
          "sha256": "269ce6dbbb27b04617956dc3c7787010cccefcc81e3e37ad87fd114cd17ef216"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d2_feedback_pulse_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 2,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.234
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d3_publish_preflight_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d3_publish_preflight_backups",
    "before": {
      "source": "reports/quality/a5_p2d3_publish_preflight_backups",
      "file_count": 4,
      "test_file_count": 1,
      "size_bytes": 38712,
      "size_mb": 0.037,
      "files_top_300": [
        {
          "relative_path": "publish_integrity.py",
          "size_bytes": 5414,
          "sha256": "17fdfb072ba06f08b096134df887ab1babdcadad823aca654fb8d41e60914ecd"
        },
        {
          "relative_path": "publish_preflight_rules.py",
          "size_bytes": 18898,
          "sha256": "fa46257f29c8bec781459be6def5dd944a16b1fc88c1888a1a2079e176f1e8e4"
        },
        {
          "relative_path": "test_performance_publish_preflight_static.py",
          "size_bytes": 1364,
          "sha256": "0922ad6fa805ffc1476af2d2d807c5709fe740a81f39d6e3e50f85f4c5a8a3ef"
        },
        {
          "relative_path": "visibility_publication_gate.py",
          "size_bytes": 13036,
          "sha256": "837315af279eef35630cd13a571aff7dbc28c04dd29867039d80bbe08964b5d0"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d3_publish_preflight_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 4,
      "destination_test_file_count": 1,
      "destination_size_mb": 0.037
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d4_core_security_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d4_core_security_backups",
    "before": {
      "source": "reports/quality/a5_p2d4_core_security_backups",
      "file_count": 2,
      "test_file_count": 1,
      "size_bytes": 10890,
      "size_mb": 0.01,
      "files_top_300": [
        {
          "relative_path": "__init__.py",
          "size_bytes": 8032,
          "sha256": "601c407fe1cd14a29ef5eb0ca353c02ec8650ccd3a8fc388b3655f9cb498e5a2"
        },
        {
          "relative_path": "test_final_quality_security_source_contract.py",
          "size_bytes": 2858,
          "sha256": "f71fb33454a37fa0c1dfb71b1b59de75e4ed0f78c9a34bbd770186793f55a17f"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d4_core_security_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 2,
      "destination_test_file_count": 1,
      "destination_size_mb": 0.01
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d5_phase_gates_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d5_phase_gates_backups",
    "before": {
      "source": "reports/quality/a5_p2d5_phase_gates_backups",
      "file_count": 1,
      "test_file_count": 0,
      "size_bytes": 556,
      "size_mb": 0.001,
      "files_top_300": [
        {
          "relative_path": "mail_service.py",
          "size_bytes": 556,
          "sha256": "c0b28825e1cb06a3a7935991bc42b091a52de1c5629d9a5892b3a449091f9f6f"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d5_phase_gates_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 1,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.001
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d5_v3_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d5_v3_backups",
    "before": {
      "source": "reports/quality/a5_p2d5_v3_backups",
      "file_count": 8,
      "test_file_count": 0,
      "size_bytes": 54747,
      "size_mb": 0.052,
      "files_top_300": [
        {
          "relative_path": "apply_p14_g2_self_p0_fix_v1.py",
          "size_bytes": 8633,
          "sha256": "31e5a418d5a12a88f0b555af75eaae0b77654230ae3f40d2600879bce0d221c8"
        },
        {
          "relative_path": "apply_p14_g_p0_silent_except_fix_v1.py",
          "size_bytes": 10523,
          "sha256": "fddf2e793e660fcaf16b040f68f08d6075a1fa931af870ca7c26a9a238af48d4"
        },
        {
          "relative_path": "apply_p14_h2_self_except_fix_v1.py",
          "size_bytes": 8796,
          "sha256": "09d0a73506e525bdc697d76daae52a1662e236602d17689d7a94e07289fb752d"
        },
        {
          "relative_path": "apply_p14_h_p1_cleanup_v1.py",
          "size_bytes": 10733,
          "sha256": "f868cbe9c7e84bb36690722a4325157b00a3634fe7cdd93942329bd2890f360e"
        },
        {
          "relative_path": "check_critical_services_phase5_gate.py",
          "size_bytes": 1176,
          "sha256": "9944d921f355a150d3a022305f30cad35c585eb889a7bffb371ac11ca198a2fd"
        },
        {
          "relative_path": "check_sql_performance_phase6_gate.py",
          "size_bytes": 1161,
          "sha256": "8db055e305fcc3e38d579f2ef7d390ff78d1b7f5f77244cbd3bdfb7e56686e68"
        },
        {
          "relative_path": "mail_service.py",
          "size_bytes": 1526,
          "sha256": "c153681dab41c0f2c36b88e5897f2cb5db403197abff0153f8f29063eb966535"
        },
        {
          "relative_path": "repair_bys360_repo_hygiene_p19b_cic_task_contract_wiring_v1.py",
          "size_bytes": 12199,
          "sha256": "8e036ce84492d861b3dfeb2d050869f058f92ed7800e2c9dd2fcf284595b690e"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d5_v3_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 8,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.052
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d5_v4_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d5_v4_backups",
    "before": {
      "source": "reports/quality/a5_p2d5_v4_backups",
      "file_count": 6,
      "test_file_count": 0,
      "size_bytes": 52585,
      "size_mb": 0.05,
      "files_top_300": [
        {
          "relative_path": "apply_p14_g2_self_p0_fix_v1.py",
          "size_bytes": 8633,
          "sha256": "31e5a418d5a12a88f0b555af75eaae0b77654230ae3f40d2600879bce0d221c8"
        },
        {
          "relative_path": "apply_p14_g_p0_silent_except_fix_v1.py",
          "size_bytes": 10523,
          "sha256": "fddf2e793e660fcaf16b040f68f08d6075a1fa931af870ca7c26a9a238af48d4"
        },
        {
          "relative_path": "apply_p14_h2_self_except_fix_v1.py",
          "size_bytes": 8796,
          "sha256": "09d0a73506e525bdc697d76daae52a1662e236602d17689d7a94e07289fb752d"
        },
        {
          "relative_path": "apply_p14_h_p1_cleanup_v1.py",
          "size_bytes": 10733,
          "sha256": "f868cbe9c7e84bb36690722a4325157b00a3634fe7cdd93942329bd2890f360e"
        },
        {
          "relative_path": "check_critical_services_phase5_gate.py",
          "size_bytes": 1701,
          "sha256": "6cb281d84ca7b83530fdec762b310aa2d83d3e6ca7f302d9dba6a76ea8fc4c17"
        },
        {
          "relative_path": "repair_bys360_repo_hygiene_p19b_cic_task_contract_wiring_v1.py",
          "size_bytes": 12199,
          "sha256": "8e036ce84492d861b3dfeb2d050869f058f92ed7800e2c9dd2fcf284595b690e"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d5_v4_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 6,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.05
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d6_message_comm_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d6_message_comm_backups",
    "before": {
      "source": "reports/quality/a5_p2d6_message_comm_backups",
      "file_count": 12,
      "test_file_count": 0,
      "size_bytes": 340851,
      "size_mb": 0.325,
      "files_top_300": [
        {
          "relative_path": "assignment_sync_service.py",
          "size_bytes": 18242,
          "sha256": "78f88fb153b7eb7e790bf36d036be9ff3b6465dd4f3ab7c7497c014b3689d0fa"
        },
        {
          "relative_path": "category_group_center.py",
          "size_bytes": 14380,
          "sha256": "6362b29b663988075c55a0770ac13ab0841eebfa1d99d73b1cfbb82df941ef02"
        },
        {
          "relative_path": "chain.py",
          "size_bytes": 17777,
          "sha256": "a8fb46828b6620311e39daebd4369a1cea897e06e191408b2605808eb4509ea3"
        },
        {
          "relative_path": "compose.py",
          "size_bytes": 11338,
          "sha256": "7ead0d1580d11d297af6ea2f8e52fabdb9677436b6697512ef7782840ade7255"
        },
        {
          "relative_path": "corporate_information_center.py",
          "size_bytes": 134122,
          "sha256": "54552464c625d7efdf51b059de84973ab17e2d6eb42120a87c117879f3d379c0"
        },
        {
          "relative_path": "instagram_portal_sync.py",
          "size_bytes": 13612,
          "sha256": "f16508a726a0219d08ce5ba9fab669b7390c4eda4b0b6e9fab039675bf7e2291"
        },
        {
          "relative_path": "leave_delegation_service.py",
          "size_bytes": 18189,
          "sha256": "5a7d627079c9de0267e24bde71618ebae26d85ceb48f8fd1c38c2af09745be2d"
        },
        {
          "relative_path": "message_service.py",
          "size_bytes": 21996,
          "sha256": "2b8dcf958c2bf7697bcffacf4c1e0b172893cf24650029ebf50790d6239893e7"
        },
        {
          "relative_path": "messages_routes.py",
          "size_bytes": 29348,
          "sha256": "3945f7011c38907ef6c87786959d60288f489ca18059055629dfd403a5cf6513"
        },
        {
          "relative_path": "query_adapters.py",
          "size_bytes": 6899,
          "sha256": "f980f3bd06ee6a5b0f3ec8436e98d177b0aff34a977b52e641932f435870cef5"
        },
        {
          "relative_path": "sync_service.py",
          "size_bytes": 34980,
          "sha256": "d5c8034be15ff4c825b386fdbd9d31afdbc41463c17817ffcb61b9f55c908f7e"
        },
        {
          "relative_path": "v2_1_6_category_period_integration.py",
          "size_bytes": 19968,
          "sha256": "51237a32abde8729da846e1c46abf83a0fd4eee354979e8a8ecd5dd5b1d4192e"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d6_message_comm_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 12,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.325
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d6_v3_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d6_v3_backups",
    "before": {
      "source": "reports/quality/a5_p2d6_v3_backups",
      "file_count": 5,
      "test_file_count": 0,
      "size_bytes": 95487,
      "size_mb": 0.091,
      "files_top_300": [
        {
          "relative_path": "category_group_center.py",
          "size_bytes": 14380,
          "sha256": "6362b29b663988075c55a0770ac13ab0841eebfa1d99d73b1cfbb82df941ef02"
        },
        {
          "relative_path": "chain.py",
          "size_bytes": 17803,
          "sha256": "93dd5c36404c40b0d46cc76982c539f70c84b0ccb839539a43ec9cd0b7a395b2"
        },
        {
          "relative_path": "instagram_portal_sync.py",
          "size_bytes": 13612,
          "sha256": "f16508a726a0219d08ce5ba9fab669b7390c4eda4b0b6e9fab039675bf7e2291"
        },
        {
          "relative_path": "messages_routes.py",
          "size_bytes": 29712,
          "sha256": "5f6c12e5a452b7a49cd52f8775010cde4ac4519a945edfb91b1ab8a785cb3ea1"
        },
        {
          "relative_path": "v2_1_6_category_period_integration.py",
          "size_bytes": 19980,
          "sha256": "63c4321e9ae3e3a9c23116c4c3c444bdc087948a70b53387adc8248b38c0d143"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d6_v3_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 5,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.091
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d7a_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d7a_backups",
    "before": {
      "source": "reports/quality/a5_p2d7a_backups",
      "file_count": 2,
      "test_file_count": 0,
      "size_bytes": 59904,
      "size_mb": 0.057,
      "files_top_300": [
        {
          "relative_path": "feedback_aftercare.py",
          "size_bytes": 26782,
          "sha256": "914f2fc38acfaa5c9e445786e5b8b53edae06d411c9a3e3122bccf4d56698969"
        },
        {
          "relative_path": "messages_routes.py",
          "size_bytes": 33122,
          "sha256": "50e490dffb30291d53f7840e21c23b1e09ac7f941d521cfd0c6068362445d00d"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d7a_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 2,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.057
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d7b_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d7b_backups",
    "before": {
      "source": "reports/quality/a5_p2d7b_backups",
      "file_count": 4,
      "test_file_count": 0,
      "size_bytes": 58203,
      "size_mb": 0.056,
      "files_top_300": [
        {
          "relative_path": "500.html",
          "size_bytes": 290,
          "sha256": "1f2cd744983f8fb51638f30df30b70be56800d6dfb5d27acc69b7d9d2a37b5a2"
        },
        {
          "relative_path": "assistant_module_access.py",
          "size_bytes": 16855,
          "sha256": "c4a5e3e014f5a2ea35f03f54ad149a521346a75e664b2ac65e76555d8a01b3db"
        },
        {
          "relative_path": "feedback_aftercare.py",
          "size_bytes": 27533,
          "sha256": "222497739e45fbfc0397ae42741b471ca8908a6e33ce134cd5d6e98c640cf276"
        },
        {
          "relative_path": "feedback_aftercare_routes.py",
          "size_bytes": 13525,
          "sha256": "39a64cfa92739b8d0d3c2286841536bab43e1f78cbd63e5abae89836c7a2c7b4"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d7b_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 4,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.056
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/a5_p2d8_ai_export_backups",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d8_ai_export_backups",
    "before": {
      "source": "reports/quality/a5_p2d8_ai_export_backups",
      "file_count": 1,
      "test_file_count": 0,
      "size_bytes": 2119,
      "size_mb": 0.002,
      "files_top_300": [
        {
          "relative_path": "dashboard_panels.py",
          "size_bytes": 2119,
          "sha256": "6d10116ae0b0cf1a7e413bee5b071dbd0250c5ecbf1eae84486ab09bb5b528a5"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\a5_p2d8_ai_export_backups",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 1,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.002
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/P0_BACKUP",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\P0_BACKUP",
    "before": {
      "source": "reports/quality/P0_BACKUP",
      "file_count": 1,
      "test_file_count": 0,
      "size_bytes": 7646,
      "size_mb": 0.007,
      "files_top_300": [
        {
          "relative_path": "conftest.py",
          "size_bytes": 7646,
          "sha256": "d021dded0159fced8ac254a341687e2e991b78af5af7969d3a741fcaf827ba8e"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\P0_BACKUP",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 1,
      "destination_test_file_count": 0,
      "destination_size_mb": 0.007
    }
  },
  {
    "type": "move_reports_quality_backup_dir_to_release_archive",
    "status": "moved",
    "source": "reports/quality/P2_BACKUP",
    "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\P2_BACKUP",
    "before": {
      "source": "reports/quality/P2_BACKUP",
      "file_count": 208,
      "test_file_count": 119,
      "size_bytes": 347977,
      "size_mb": 0.332,
      "files_top_300": [
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_android_responsive_baseline_p5a.py.disabled",
          "size_bytes": 956,
          "sha256": "897e7089763e89f7cd83e04e47531e2da3080fbfbb56ca75e577a5802aa8de40"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_android_responsive_final_evidence_p5f.py.disabled",
          "size_bytes": 590,
          "sha256": "59324eae94a2e4422049db06c1b6eb6f5d8dc7e70e127acb1643dcc7f8e7c71d"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_android_responsive_inventory_precision_p6c.py.disabled",
          "size_bytes": 696,
          "sha256": "c5a8ac6772d2d14dd5db211e0c94d9ba08c82819cfcd222ba5435557f6108940"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_android_responsive_release_suite_p5d_v2.py.disabled",
          "size_bytes": 550,
          "sha256": "f82b92d015e8ba5b4e03dcafca510ba6bed5cb05d8c022e19b3f6653a3fedff7"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_android_responsive_visual_regression_p6a.py.disabled",
          "size_bytes": 791,
          "sha256": "214ac5df7cf0b806105560c3fa87ed42f8ca0059a76d493034d74308874b08b3"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_android_responsive_visual_uat_evidence_p5e.py.disabled",
          "size_bytes": 559,
          "sha256": "1724dee8430fc0b7313e45254bd532955f6118ea60fd6f2b4259ae58a190cf11"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz10_contract.py.disabled",
          "size_bytes": 2168,
          "sha256": "28a4f7f5daaba1848edd8dcdff214c0aa27da0a2a9a97be8626a4834776fb97c"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz2_contract.py.disabled",
          "size_bytes": 735,
          "sha256": "661b1d27f3ed05973df16d990fb01b9d4f8548457d9c3d1fcb79d3850cc06670"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz5_contract.py.disabled",
          "size_bytes": 2393,
          "sha256": "917148fae177295c25e0c6417fbb0bb14eb7e7e9a6f61df80adf7303087fd862"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz6_contract.py.disabled",
          "size_bytes": 1608,
          "sha256": "7653c06e3355fe6015da24d7d4becfd50b4c8fce3f5ceb48649266d7230547bc"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz7_contract.py.disabled",
          "size_bytes": 1681,
          "sha256": "97df77067683750e6d1f0b83670d53d3773bc772a75d0c9e20db96c4e8c85f09"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz8_contract.py.disabled",
          "size_bytes": 2171,
          "sha256": "0f56b90c118b50202936818282502ca2cb185f4d90ba5e988caf9aa300383ab1"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_core_refactor_faz9_contract.py.disabled",
          "size_bytes": 2140,
          "sha256": "4413808396bf047189a11a9d8a0a222b443c4a0f0b555c160903d08ae766513a"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_home_phase1_contract.py.disabled",
          "size_bytes": 1759,
          "sha256": "9adf99d4ed9f34c44dddbe3f61645662720c535eb576773de103a3b7ff135810"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_message_faz1_smoke_contract.py.disabled",
          "size_bytes": 6087,
          "sha256": "be3333e0e40be379f3dbfe079a401aa4131420d2e0b4fe21d6b98c6b260f00b0"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_message_faz2_service_contract.py.disabled",
          "size_bytes": 2304,
          "sha256": "a42ee87a19056f9552a7ebf6d9f7cf0ab39650e6b2d8477fea2bcecc98823c57"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_mobile_api_release_evidence_p4e.py.disabled",
          "size_bytes": 933,
          "sha256": "27256f7aac81b9ebe6cb534ba584a665b5c51f67a258531da616d80d113ae300"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_mobile_api_request_smoke_p2c.py.disabled",
          "size_bytes": 748,
          "sha256": "bcd0fe10dae23f8ed184547f4f3cccf5a2820bab128ca0a5cea1652c9610e398"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_mobile_api_role_boundary_matrix_p4b.py.disabled",
          "size_bytes": 644,
          "sha256": "b46fe815bcf0a13713b32373eebe114b0ee8c56c798ede4239fee1fb8ae83ecc"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v2.py.disabled",
          "size_bytes": 650,
          "sha256": "e97a881eb7c1e5d448956d0403636630fe90326d6474bd94930d7f0df00d81d1"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_mobile_api_security_evidence_p4d.py.disabled",
          "size_bytes": 1377,
          "sha256": "21fa58f8949fd9657b5f5cdd2488e1bd7adebc80a80f12c8efaeef56da3ca76d"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_portal_service_faz6_contract.py.disabled",
          "size_bytes": 2726,
          "sha256": "a4abc0f1303109f75a6a62739b193ff472268a264478b81db87a9dac3ccd4bbd"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_settings_faz0_live_contract.py.disabled",
          "size_bytes": 2321,
          "sha256": "41850f5308d983c8701dbf5ab4aac89e0305500dd0f9f0209ce176e8b74111c1"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_settings_faz2_service_bridge.py.disabled",
          "size_bytes": 1924,
          "sha256": "89f298bb219bb9993458eca7053d387af4b056cb4f33312716edf6e3c48b4fe4"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_settings_faz3_snapshot_contract.py.disabled",
          "size_bytes": 1397,
          "sha256": "2f3305428acf4b1426fdd5e2ab85c5d033c5ee99591eb98f463df9b04c69c1dd"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_survey_faz1_smoke_contract.py.disabled",
          "size_bytes": 5920,
          "sha256": "d4e470ab8bd44e0b65d4e2c3d763fbd29d4a416dbaf4c0bd2ff9d03890de27c7"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_survey_faz2_service_contract.py.disabled",
          "size_bytes": 1948,
          "sha256": "736bc3c32ddc996ea50e432884af9269b34eb185c549c240a057263ece3553df"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_survey_faz3_route_service_bridge.py.disabled",
          "size_bytes": 2455,
          "sha256": "5ce887308d5ef560c9e934401409ad8ed0e9296b4bd614695461c614a489cfd5"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_survey_faz4_read_service_contract.py.disabled",
          "size_bytes": 1846,
          "sha256": "09621d0731964f070adb922344be66e89f84f8d32487a7ba8896f975a4191f04"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_survey_faz6_target_access_contract.py.disabled",
          "size_bytes": 1544,
          "sha256": "2fea0e3b95e5825e22db399cda7ecb50029762740c280470581169dffbfcde4a"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/architecture/test_survey_faz7_submit_contract.py.disabled",
          "size_bytes": 2290,
          "sha256": "bb9280714122a2f0d2d65c52bc9a2f82e735f885f10398afa67520dc7351b306"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/communication/test_communication_template_presence.py.disabled",
          "size_bytes": 1036,
          "sha256": "9193dc55c086a964959dc0b456968ae0bd67821a480eecd77a2cd667fd7b3bbb"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/communication/test_phase9a_route_contracts.py.disabled",
          "size_bytes": 534,
          "sha256": "60888e9e883e0d3f9ee755ad298fec19a6175be321bb2e5cea44a53f26e8dec9"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/expert_review/test_phase10_expert_final_gate.py.disabled",
          "size_bytes": 1221,
          "sha256": "006a865477a2f581e2800b0c6d9574fe0e6bd7c9d79c54cfa57fb638ff8971a0"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/expert_review/test_phase13_final_expert_review_package.py.disabled",
          "size_bytes": 1011,
          "sha256": "92ea51f2871181544954c3de841b40be08166d440292edbf3268aa5d23405157"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_final_quality_live_backbone_release_contract.py.disabled",
          "size_bytes": 2587,
          "sha256": "d12bf95a0a181fb5e041f8112891d2405148596f6a60804032fec9ef449d6d62"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_auth_login_smoke_v5.py.disabled",
          "size_bytes": 1196,
          "sha256": "4b49c04512d267f7598483dbcce7a2f6e61afd415a191e9e8205fcfead13d8ad"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_closure_freeze_v19.py.disabled",
          "size_bytes": 2206,
          "sha256": "9fefca0939ed5cab5b748ebc3867c6f1fa9675eeee5575273ccad23624bc1de5"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_closure_freeze_waiting_mode_hotfix_v19_1.py.disabled",
          "size_bytes": 2255,
          "sha256": "05a3369b82c54ff1d1e632a0d97675f38f810467a660d37154e7eea270abb9a7"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_critical_pages_smoke_v7.py.disabled",
          "size_bytes": 2023,
          "sha256": "2dd46468da071f2e5d28a77af46b061fe0a34baabc30113bb7261d8c329f4757"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_deployment_runbook_rollback_v16.py.disabled",
          "size_bytes": 2070,
          "sha256": "31c7f3d5f2a07a528c0b4f2a454acec8ef5f7b0e378ed55753c28926d072ae31"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_final_regression_matrix_v9.py.disabled",
          "size_bytes": 1953,
          "sha256": "7c1ae78891c2f80000712cd08be27b2c2905a36b81e2c6aa0d94af260d5b590e"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_integration_smoke_v4.py.disabled",
          "size_bytes": 2223,
          "sha256": "44b4b301c9dee6d25fea8fe17af5791bf867c74dac8ecd02ad1d61eb923c2b22"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_legacy_integration_scope_v8.py.disabled",
          "size_bytes": 2002,
          "sha256": "031f1926d0dc562aebfdf3d961f106d8aabc8a4b2188e572b6774a3b9451aeb7"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_live_server_preflight_v17.py.disabled",
          "size_bytes": 2441,
          "sha256": "5659a9eb769bb24c6739f38cd6562773946fffaa6ab85e0372d9b2ed7f00378b"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_real_login_smoke_v6.py.disabled",
          "size_bytes": 1835,
          "sha256": "4e709fb5e6dc22c2a5495f0f20cd08a801aa2f562c04bb929954d8c92cfb8d5d"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_release_candidate_verify_v13.py.disabled",
          "size_bytes": 1703,
          "sha256": "98afd84fc60e962abc6496fcd150f4ed03386381f43756cef9508421abcd949d"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_release_evidence_bundle_v14.py.disabled",
          "size_bytes": 1785,
          "sha256": "789dae33af157d303a16bfe40561e11219967af399c09a7544ee82706c7b16ba"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_release_manifest_dry_run_v11.py.disabled",
          "size_bytes": 1777,
          "sha256": "c398354be7bf8bcff1c7be6d00f41f5c3cbf1b0faa5f7f7cbc8c50bb3246b77a"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_release_package_builder_v12.py.disabled",
          "size_bytes": 1575,
          "sha256": "d8aed466b573b2e12a7ff03d8e5f455711f435651d9c6540ee0035c4fd4eb654"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint2_release_readiness_v10.py.disabled",
          "size_bytes": 2098,
          "sha256": "c72cc6d1342d96244ff910918d9ad7f381ccc942a4ab3192bb087d5fe08e640d"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_closure_freeze_next_stage_phrase_hotfix_v6_1.py.disabled",
          "size_bytes": 1081,
          "sha256": "33de5196191525708ed7dd3ba4552b9b733929dd33bc537825e45c5b4a127db4"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_closure_pilot_acceptance_freeze_v6.py.disabled",
          "size_bytes": 2285,
          "sha256": "015f091dbd2f4641cfb1ab81ce41a108dfe893af09b43e3d14195b0b5acc6132"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_corporate_approval_decision_consolidation_v5.py.disabled",
          "size_bytes": 2261,
          "sha256": "67379f62b922a66fc168adf7e6e16ebaad2d308f089456889a7a9f59d8135fdf"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_corporate_approval_minutes_live_note_hotfix_v4_1.py.disabled",
          "size_bytes": 1417,
          "sha256": "53975fe0d6af9bb92ccb7501ec510e66bc62512a2abbde7f17bb6e1af61624d2"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_corporate_approval_pack_v4.py.disabled",
          "size_bytes": 2113,
          "sha256": "724118cd8ec9a90fb76db4fd0102bedd699274ae00c5da60d632ca0ace45549c"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_pilot_execution_matrix_v2.py.disabled",
          "size_bytes": 2558,
          "sha256": "7977ffc1ef3d29547ab7c7833be69d6ab25b954d78409072553b92cb20e646a7"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_pilot_triage_board_v3.py.disabled",
          "size_bytes": 2297,
          "sha256": "a8e794e9ff6021bda6ac01e174d5e8ecd1c2d2914075c4220b06af06caf2dc99"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/integration/test_sprint3_uat_pilot_plan_v1.py.disabled",
          "size_bytes": 2465,
          "sha256": "2751e6a803afc7f6a6e9c26ff6e06009e18d9fc5e8c296208686c0c6e583fde4"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/ops/test_live_ops_contract.py.disabled",
          "size_bytes": 1389,
          "sha256": "6dbacc6a4ee62707afa87881530e1b1950c41178d3e703fd26245a1004983fed"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/release/test_final_quality_release_chain_contract.py.disabled",
          "size_bytes": 2688,
          "sha256": "95992ca946963b98f599112f9d512ee51d9f043cfc12142737f9ef397f6b409a"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/release/test_final_quality_release_report_contract.py.disabled",
          "size_bytes": 1447,
          "sha256": "435dd9c61769ef6aec3044d93948509320832775819f537c1e26494bedfa4a64"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/release/test_phase11_release_clean_gate.py.disabled",
          "size_bytes": 939,
          "sha256": "877091297e841427163774a2ad26fe224dfd1ca8aa08fb2f273165d69905bf61"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/security/test_final_quality_security_release_contract.py.disabled",
          "size_bytes": 2134,
          "sha256": "18323a361a05f7af51882b4c55f5459cf6b932755d916282473f05d83df891fc"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/services/test_final_quality_home_weather_contract.py.disabled",
          "size_bytes": 1798,
          "sha256": "d14ce913cdc564ea698a258bf767cb7af9cbbe6f9c2004577d1a5debeee7c2b9"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/services/test_final_quality_live_source_contract.py.disabled",
          "size_bytes": 2478,
          "sha256": "35e7ece10d7b78f901658612ebc6419c5a1d138708efb5eca4afacaf6d6858a4"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/sprint2/test_sprint2_coverage_baseline_v3.py.disabled",
          "size_bytes": 892,
          "sha256": "b67aa95cf63e9f293ef4ad82001dd7b057c00b3fa5cc8c7d5a2756ee12afee69"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/sprint2/test_sprint2_critical_guard_tests_v2.py.disabled",
          "size_bytes": 2522,
          "sha256": "44e1dd8d3ee6ae0683e2e8e9a34d03bd59c0bb2235515e379ec7b7912c1402b7"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/sprint2/test_sprint2_test_infra_v1.py.disabled",
          "size_bytes": 1176,
          "sha256": "5898f6a03829be16f24f81dee3f2192f043c5328d9865eead63b23839bb7cf46"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_ai_analysis_visual_reports_static.py.disabled",
          "size_bytes": 1067,
          "sha256": "9591d9751da8393dad81bf90cf2363be8cd5a78f97386d0daef800c62999d84a"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_ai_final_live_hardening_static.py.disabled",
          "size_bytes": 1332,
          "sha256": "5f0dcda2a06fc38c9945e90ba7762bf3b21a78c454b7a5310768eccf46dafa0b"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_ai_visibility_gate_static.py.disabled",
          "size_bytes": 1492,
          "sha256": "1cee8c264cd90484cd4f770d18b48ff497a3f41cf93c9ffb8ffaf1469a30a583"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_async_task_infrastructure_static.py.disabled",
          "size_bytes": 1129,
          "sha256": "fcb4f745090e382a31ae1b35c251d8cd65291ce61d06831b02096a2f67329cbb"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_claude_phase5_smoke_routes.py.disabled",
          "size_bytes": 3290,
          "sha256": "c8299d3da56c8e6c6f0fa3c379c47183ed1502c68f9dd7f103d2e9312e3e54a8"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_hr_leave_attendance_real_post_static.py.disabled",
          "size_bytes": 1682,
          "sha256": "72b09fde2d7b581b6a614a08bc9490518d2289fb77cc29e58395d62cd8986d97"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_institutional_dashboard_route_static.py.disabled",
          "size_bytes": 1056,
          "sha256": "951bc24f1a5bcf48d6394fa175aefcd50ca9bd3b3e0b2113b77007bd11e36854"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_performance_assignment_rule_gate_static.py.disabled",
          "size_bytes": 1603,
          "sha256": "176993b190fe7f003835afcdb48d95c844af6d99c7fa25a588886c861ab7247c"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_performance_core_health_dalga8_static.py.disabled",
          "size_bytes": 1991,
          "sha256": "2749de539aa7282e78b0437795d819945335336f41307708c81e73223be9306a"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_performance_phase5_ui_copy.py.disabled",
          "size_bytes": 1160,
          "sha256": "960d0c5d5a52037aa85bdf223e954387899dec231d282d7db0b580a0eee43855"
        },
        {
          "relative_path": "tests/_archive_a5_obsolete/20260612_090923/tests/test_performance_visibility_constitution_static.py.disabled",
          "size_bytes": 1535,
          "sha256": "dc0ab8b329f03b7691ae535e9f8dc7e4b52ebd316919274dff9515b8323522bb"
        },
        {
          "relative_path": "tests/architecture/conftest.py",
          "size_bytes": 6280,
          "sha256": "70b0211c417a1ffa92bc10f28d058a7a065883770020db005e388e487a3b27f8"
        },
        {
          "relative_path": "tests/architecture/test_ai_dashboard_panels_split.py",
          "size_bytes": 1113,
          "sha256": "82109c3f859cc68a7e862d111e10f0307a636fb88ba1258039fbada1cac0c5ca"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_core_styles_p5b.py",
          "size_bytes": 1048,
          "sha256": "e95c3dcbd9539f012a854bb93ce41e4f71cd5b80c62e37210e51b1f1b6d2ca90"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_release_suite_p5d.py",
          "size_bytes": 308,
          "sha256": "51ec7501b802bb468891cff568db2270817337e8a20d755ec9695aeff0423c42"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_targeted_templates_p5c.py",
          "size_bytes": 325,
          "sha256": "39b6b95b420cf8139c0983136255ce104a1669b0fcd25e7632105e4e098a2219"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_visual_regression_evidence_suite_p6b.py",
          "size_bytes": 892,
          "sha256": "93bc0a9244eb1af21484d133a2bc9249092ab4ded432710d937e170a45f9aab1"
        },
        {
          "relative_path": "tests/architecture/test_android_responsive_visual_regression_evidence_suite_p6b_v2.py",
          "size_bytes": 901,
          "sha256": "75059f7887ecd4fd0d41f380284bd844af8b4c67c4fcc7b44b0c1432df0fc0f4"
        },
        {
          "relative_path": "tests/architecture/test_architecture_scope_p2e.py",
          "size_bytes": 1016,
          "sha256": "ab5a77e25c7612d022302e5db8a025d11e61d4f2ceb59bde15c76a4ddd065df3"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz1_contract.py",
          "size_bytes": 936,
          "sha256": "9fa595a903a06b1a9742430957e9e08f331b7b20ec230ecfa6e07473ce3ffb91"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz3_contract.py",
          "size_bytes": 713,
          "sha256": "872fe5c2744b4a3cde2987bef06b031dfc8432cc88ed90f1905aa40313233f83"
        },
        {
          "relative_path": "tests/architecture/test_core_refactor_faz4_contract.py",
          "size_bytes": 876,
          "sha256": "412905364ef4a2501ed66efa9e09084cbeadd4398e766c6d5343c5662050c531"
        },
        {
          "relative_path": "tests/architecture/test_login_home_redirect_contract.py",
          "size_bytes": 1367,
          "sha256": "f4bb6d1f6fd04dddd969f65a892d08ae1e043011ed30b48f305c514dea9b08f3"
        },
        {
          "relative_path": "tests/architecture/test_message_faz10_closure_contract.py",
          "size_bytes": 1868,
          "sha256": "688f80213503beb4468a3948d5d5c084bc0eacde5e696a853acaabc6f9e7d4f9"
        },
        {
          "relative_path": "tests/architecture/test_message_faz3_route_service_bridge.py",
          "size_bytes": 1313,
          "sha256": "4df4a29ae2bd1cf7256130e5c976027da70957f7afb39b1761eeb7aa63390f06"
        },
        {
          "relative_path": "tests/architecture/test_message_faz5_compose_contract.py",
          "size_bytes": 1786,
          "sha256": "b5dedaeeb161f3e3e3f6e5d7589f2c6d3de8da33d8defc527ee11d9373981839"
        },
        {
          "relative_path": "tests/architecture/test_message_faz6_thread_live_contract.py",
          "size_bytes": 1009,
          "sha256": "4f9ded20a931dd66b9fb80e293dd312d41d4bb5cb544db1723545998f7939e6d"
        },
        {
          "relative_path": "tests/architecture/test_message_faz7_typing_reaction_contract.py",
          "size_bytes": 1531,
          "sha256": "b957f3083b92ff5545ccf15a58c35919bebd6aeb30400b8b2e41a8f8b619ea68"
        },
        {
          "relative_path": "tests/architecture/test_message_faz8_state_bridge_contract.py",
          "size_bytes": 1470,
          "sha256": "e0fe40dd403baf5d8553c1c6e98a65139b8135a1d527d2c3e95390233e2e3f08"
        },
        {
          "relative_path": "tests/architecture/test_message_faz9_send_bridge_contract.py",
          "size_bytes": 1550,
          "sha256": "11de646aa41ad5d5f981432a3ae5b5fb933f0939fdb34369a1e4e4593de0f40e"
        },
        {
          "relative_path": "tests/architecture/test_message_live_contract.py",
          "size_bytes": 4498,
          "sha256": "c26874bd6e56d7ec1577aa511fbe7738cae01745307f84688ab99af2b1cd2358"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py",
          "size_bytes": 629,
          "sha256": "ac343a35e43411608794177040081342eda394caeed7b60246579b0c9a1edb6c"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py",
          "size_bytes": 635,
          "sha256": "295a7eb4af5bc9abdbb60280e0fee952a44c303f5f52fdd79ab51323a87a688b"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_behavior_smoke_p2b.py",
          "size_bytes": 2988,
          "sha256": "783ceb03280fe34eb7c2c39cdcf7158bd95811a20631db53960451d09433b711"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_contract_p2a.py",
          "size_bytes": 1223,
          "sha256": "44cadaf64e5be4c738cfd9af797040dc920cb2f6d2658dbf1318d5a88ab17e6f"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_performance_response_p3e.py",
          "size_bytes": 692,
          "sha256": "843c9763f0bba286a5433a6a9b5099e5b64dea9242e04d9f8d2cfb3668866e40"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py",
          "size_bytes": 720,
          "sha256": "8fadecb3933bcd412abcb237b2edd38bbe0d1591bd0a890cd2a00d1770fca7fc"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py",
          "size_bytes": 726,
          "sha256": "432ddfd5f8922314ad599c96570714b1eee79d08106ee2559d08ca01886a1d03"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_request_level_smoke_p2c.py",
          "size_bytes": 1072,
          "sha256": "60ef9a670d4f215242983a4ec8897f46207c5732da9d692cbee66eee13b2ff5b"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py",
          "size_bytes": 1075,
          "sha256": "a1882ffce55e6d84f631ce3ab1302dd824e449ae8d4e3086da6049ca8d362386"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_request_scenarios_p3a.py",
          "size_bytes": 840,
          "sha256": "c95e1744f9ccc041846f8f13b483c18d5cf471043bd89bbf4b822baee1d261a5"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_response_suite_p3f.py",
          "size_bytes": 823,
          "sha256": "d8ad791e2989d609efc74e5f970426fd9a2daf8369c9580cf953fded185f5272"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v3.py",
          "size_bytes": 650,
          "sha256": "5cde53604f0256571e47b377016f28cc0cb64772cd99bf6b86ae67503aa99ef9"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_security_suite_p4c.py",
          "size_bytes": 1156,
          "sha256": "3f1ac66d2c64e2ab062fa97f4a1f50408388f5e63d21ff0ac0e44d5d06283005"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_security_suite_p4c_v2.py",
          "size_bytes": 1165,
          "sha256": "da8c9f26684cc060356c985ba8b98d5ef5243d97368ea4fecf423334dc5c8d2e"
        },
        {
          "relative_path": "tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py",
          "size_bytes": 726,
          "sha256": "19f9f2bd255a7376336629c8f39623429babef45846fb6115515386b93c5cdf2"
        },
        {
          "relative_path": "tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py",
          "size_bytes": 635,
          "sha256": "dfc0d7018651292eb594c551c5aec9d1c4d083b1ccc4dbff29b2f00c37f755b5"
        },
        {
          "relative_path": "tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b_v2.py",
          "size_bytes": 641,
          "sha256": "b74fff691848c5cc6fccbc552b2d5efac3e060f63fd05ef959c9bddf34ebf373"
        },
        {
          "relative_path": "tests/architecture/test_pytest_standard_p2d.py",
          "size_bytes": 711,
          "sha256": "0e7b83a7798f059a07ef850bc796237243361dc0c6ce324f201f983a7b74a0f3"
        },
        {
          "relative_path": "tests/architecture/test_settings_faz1_service_contract.py",
          "size_bytes": 1168,
          "sha256": "c1539c6fbdf5a5bfb51ec21244bf48a03730fb6cb8bc6775751a4866f6202f6c"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz10_closure_contract.py",
          "size_bytes": 1522,
          "sha256": "ef47d8d3e74d2fe75f021a15733c4afffabc80f87825253a72471dd4f6362a49"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz5_results_service_contract.py",
          "size_bytes": 2230,
          "sha256": "349b4dcdfca8e0f3a73173aeb619f71daa3e7180b69f5c504f060d2f4cdf9ff4"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz8_submission_bridge_contract.py",
          "size_bytes": 1546,
          "sha256": "5c9ed5fb6e21055a80ed748b16ff2d52134b2be9f1f2e703218a679199aff932"
        },
        {
          "relative_path": "tests/architecture/test_survey_faz9_state_bridge_contract.py",
          "size_bytes": 1239,
          "sha256": "491734279e999ca0e813720cab41b8f823c108d843a9a9529f8d9ef275506465"
        },
        {
          "relative_path": "tests/architecture/test_survey_live_contract.py",
          "size_bytes": 1627,
          "sha256": "0cb1f0f9a7f6ecbcff321a9c0dd75cac74418eee9195bc7779132364b4afc0b1"
        },
        {
          "relative_path": "tests/behavior/test_async_pulse_refresh_behavior.py",
          "size_bytes": 1197,
          "sha256": "9bd6efe7cca91accdd7e3cb85ed2dc4e28b8e765693db60d8c6f9fb38c207eec"
        },
        {
          "relative_path": "tests/behavior/test_feedback_campaign_behavior.py",
          "size_bytes": 4935,
          "sha256": "86f9d48b1c2683d3d069964e5539f36e006d8f986b6970607097426f9fecf811"
        },
        {
          "relative_path": "tests/behavior/test_hr_date_rules_behavior.py",
          "size_bytes": 628,
          "sha256": "36f25ccaa3fdff93dbf51d81fbd58e6e8113067792a291961379a721585921ad"
        },
        {
          "relative_path": "tests/communication/test_communication_route_contracts.py",
          "size_bytes": 3110,
          "sha256": "815779bc5b1152f631a10e884edf70178df128d16d72fdb2ca6907ab1701b846"
        },
        {
          "relative_path": "tests/communication/test_feedback_contracts.py",
          "size_bytes": 1917,
          "sha256": "2c8990ad770c34075909f6cf31a0e1d6521c97160c7a21f6799deda452270dcb"
        },
        {
          "relative_path": "tests/communication/test_phase8_route_contracts.py",
          "size_bytes": 439,
          "sha256": "a4bb780f67cc7ef3db9660cded158a1f2206c6e0884d088ff45839f8c4520652"
        },
        {
          "relative_path": "tests/communication/test_phase9_route_contracts.py",
          "size_bytes": 1837,
          "sha256": "c0a8aba9e40f31aee88d1f45e52719226626f5e9df428210a0e09109fe5341e6"
        },
        {
          "relative_path": "tests/communication/test_phase9b_route_contracts.py",
          "size_bytes": 1256,
          "sha256": "32ca7bda63c33a9ac45cc1f3fa88d10a50b9a17d3c17a89796db490e8e7582df"
        },
        {
          "relative_path": "tests/communication/test_phase9c_route_contracts.py",
          "size_bytes": 366,
          "sha256": "b6cb82edc5c6dd32db63a11075fb922fe0e2066bc0f7d94d504f593b2a0ad657"
        },
        {
          "relative_path": "tests/communication/test_phase9d_route_contracts.py",
          "size_bytes": 366,
          "sha256": "882f73968b7d5e229c1567dac277121e195a266a0acbe961d7290f25d188807d"
        },
        {
          "relative_path": "tests/conftest.py",
          "size_bytes": 2920,
          "sha256": "d4e1d8fc0cc129247b2a4156e4b6db76d7fbc9840174b5db0bedec7824194b5f"
        },
        {
          "relative_path": "tests/critical/conftest.py",
          "size_bytes": 207,
          "sha256": "78a099706a795fdf89b0941e442a79b0f366c2435a7c6d32797d27b4ddf4cee2"
        },
        {
          "relative_path": "tests/critical/test_claude_phase5_critical_contracts.py",
          "size_bytes": 4203,
          "sha256": "b54136636f93673c25c355616e93dde705e6712de3efd990b7d22651b05fda19"
        },
        {
          "relative_path": "tests/critical/test_claude_phase6_sql_performance_contracts.py",
          "size_bytes": 2102,
          "sha256": "e317277f5375b7f0e8e6ed4a76de4df9db889ea60150780dfecfac2bfa7c32f4"
        },
        {
          "relative_path": "tests/critical/test_claude_phase7_final_gate_contracts.py",
          "size_bytes": 973,
          "sha256": "179b1deb0e4157d28a3fc2ddb89668c3d85c55f81215789b127767407017043c"
        },
        {
          "relative_path": "tests/critical/test_v58_claude_roadmap_smoke.py",
          "size_bytes": 1561,
          "sha256": "1df645be1a18e8f2d1d67f767b9fef4cb451ff738edfcab4618b58043373786c"
        },
        {
          "relative_path": "tests/critical/test_v59_4_assistant_shortcut_context.py",
          "size_bytes": 1366,
          "sha256": "365bec4e116867f92badb1a67e4cbf1956ab574fc8c051f50c2afb8ccc07d7a3"
        },
        {
          "relative_path": "tests/critical/test_v59_broad_route_smoke.py",
          "size_bytes": 3076,
          "sha256": "6c89d9507d849994fa011582698f6bcccb3c7a07bbb37d83d698b568da48cf20"
        },
        {
          "relative_path": "tests/docs/test_docs_expert_review_contract.py",
          "size_bytes": 1201,
          "sha256": "f9744d4f964580ad5dda9ffbbfa420ef40e5b5ebc039cc501af973d35da03ba0"
        },
        {
          "relative_path": "tests/integration/test_feedback_http_behavior.py",
          "size_bytes": 564,
          "sha256": "f18e2fdf3fd72a1edfcfda7cbd1aef9cbf6eca7a9c75e934ccc4a015b8d2b880"
        },
        {
          "relative_path": "tests/integration/test_final_quality_live_backbone_contract.py",
          "size_bytes": 3668,
          "sha256": "35d5d533edecc9b17d5ed4f45d312c450bd6fd929f46650a1665ad926d5c8cfa"
        },
        {
          "relative_path": "tests/integration/test_final_quality_live_backbone_sources.py",
          "size_bytes": 3169,
          "sha256": "b9e7ad2fb3b48649e04f8f879e120ea30968e2bdfcf5bca549991eca5710fb3c"
        },
        {
          "relative_path": "tests/integration/test_http_core_smoke.py",
          "size_bytes": 1446,
          "sha256": "7f406d72ca2df2625546f18d8a71becc4e8c586867fa7a96cb434b718813c9ad"
        },
        {
          "relative_path": "tests/integration/test_http_db_core_flows.py",
          "size_bytes": 4880,
          "sha256": "025e7a05c048c1c16ff6298df4046cb72eec2399c5e31bccbd5f522592d96cce"
        },
        {
          "relative_path": "tests/integration/test_sprint3_pilot_triage_board_test_syntax_hotfix_v3_1.py",
          "size_bytes": 814,
          "sha256": "161b0794f4e5c655fe9672507ac2c95e8b291ee4de638b302130d6103b4b4502"
        },
        {
          "relative_path": "tests/load/bys360_test_users.example.txt",
          "size_bytes": 115,
          "sha256": "6bcb25ee25b86e3fddc9d512f8f1309282ccb92c5e22e4fc71d9bf70a42d8072"
        },
        {
          "relative_path": "tests/load/bys360_test_users.txt",
          "size_bytes": 230,
          "sha256": "3461a2dedf8a04634da49ee1c9b680096db28619dfff4f0fba1c8f61ec76e49b"
        },
        {
          "relative_path": "tests/load/locust_bys360_phase4.py",
          "size_bytes": 2044,
          "sha256": "cc4d39863ec5fcf2485753879cc834ac6efa27f5caabd0794e90f41c6afb5929"
        },
        {
          "relative_path": "tests/load/locust_remote_auth.py",
          "size_bytes": 1433,
          "sha256": "d2da7afc461c55582fe601503559b97829ef72dcad22fec81cb092257a295576"
        },
        {
          "relative_path": "tests/load/locust_remote_auth_pool.py",
          "size_bytes": 4194,
          "sha256": "be155686da5c4b3016141d21fa4cf77f993bd4e9e7562988ee392f288e1ae41a"
        },
        {
          "relative_path": "tests/load/locust_remote_auth_strict.py",
          "size_bytes": 3163,
          "sha256": "9ac3cfef98c1c3046f41290370f745b5683d0feea3032c41ba38e96a73aeb7ac"
        },
        {
          "relative_path": "tests/mobile/test_mobile_domain_contract_p2a.py",
          "size_bytes": 2580,
          "sha256": "009b693392db00f2ea2791078becc881992b7bca86e1af616e0a4d564c183eba"
        },
        {
          "relative_path": "tests/performance/test_critical_performance_routes_smoke.py",
          "size_bytes": 4333,
          "sha256": "3c0ff6bee4ec386c4d262552c6d3c7f8b9957a8b0034b035429f585a2e1c24b9"
        },
        {
          "relative_path": "tests/performance/test_performance_completion_phase1_rule_center.py",
          "size_bytes": 1870,
          "sha256": "6e2e1921667ff4be61d644a2361aecd2a1ff9820e3c77abcd7686411e1a45876"
        },
        {
          "relative_path": "tests/performance/test_performance_completion_phase2_category_center.py",
          "size_bytes": 1633,
          "sha256": "acd3232534a0d2f198c658c6537f4b0169b10b77e6d770a8aa71af9520dde3f2"
        },
        {
          "relative_path": "tests/performance/test_performance_completion_phase3_visibility_scope.py",
          "size_bytes": 2341,
          "sha256": "24116148458b974d8f380c9b4a65a3f9023525e1cb0251fa3f0f8589ce72a4f8"
        },
        {
          "relative_path": "tests/performance/test_phase12_performance_rules_contract.py",
          "size_bytes": 3449,
          "sha256": "07522fa6551c9b40b15d0c205e60c057177fe4aa067b201a735055628b9e897c"
        },
        {
          "relative_path": "tests/quality/test_quality9_ci_safe_contract.py",
          "size_bytes": 2266,
          "sha256": "5fe0bbfb6db14f0d5e6b6390f25c1c8d6a8f342b624e9e4ccc5a76f84bb599ec"
        },
        {
          "relative_path": "tests/release/test_final_quality_release_evidence_contract.py",
          "size_bytes": 2754,
          "sha256": "82b304475e014b2012eead5ada2f0a9b1ed685906460ea0b18d2faebaf3a2fbe"
        },
        {
          "relative_path": "tests/security/test_admin_path_guard_contract.py",
          "size_bytes": 564,
          "sha256": "3abcc967d11ef620a637cbc47848d4ee461d4d07b236dad656a4c0f27df6c6b8"
        },
        {
          "relative_path": "tests/security/test_audit_observability_contract.py",
          "size_bytes": 946,
          "sha256": "9acd015d34f4d0d3c2e96cb58f4cb6d12e4f0ddb98590a4104d502de0741cc05"
        },
        {
          "relative_path": "tests/security/test_final_quality_security_compliance_contract.py",
          "size_bytes": 2719,
          "sha256": "e36a5a958a7dc88f488f19b312bdddec157b1c2c12e741264e1cf5ea85ab4180"
        },
        {
          "relative_path": "tests/security/test_final_quality_security_source_contract.py",
          "size_bytes": 2858,
          "sha256": "f71fb33454a37fa0c1dfb71b1b59de75e4ed0f78c9a34bbd770186793f55a17f"
        },
        {
          "relative_path": "tests/services/test_final_quality_performance_rule_matrix.py",
          "size_bytes": 2637,
          "sha256": "a1ed2521bee858b78584b4f6cdb092e2a6193f1d43c23166e04a97691f7851dc"
        },
        {
          "relative_path": "tests/services/test_final_quality_performance_visibility_contract.py",
          "size_bytes": 2228,
          "sha256": "c78c0dffd83eaf2a8d5398b15898a2cbd43a0c22efb46122ea03ef6e499d28f3"
        },
        {
          "relative_path": "tests/services/test_final_quality_service_contract_manifest.py",
          "size_bytes": 2600,
          "sha256": "8cb7aead735fbe6abbb11dcff600690893dae27773103f2d5e276569305aff94"
        },
        {
          "relative_path": "tests/services/test_final_quality_third_manager_modes.py",
          "size_bytes": 1621,
          "sha256": "9367418c9d1c1ddd684bb1981a4c539965625bf3fd4f8e39f000e7a6ee9a5b03"
        },
        {
          "relative_path": "tests/services/test_leave_delegation_contract.py",
          "size_bytes": 2440,
          "sha256": "4ac5c134001af4d90e7bab5ea3b9b6a2c35bf35f1101c1e53d8b3068f53f803a"
        },
        {
          "relative_path": "tests/services/test_performance_assignments_contract.py",
          "size_bytes": 1530,
          "sha256": "280bdd550dd694e22aba9de07fc373d091912212c6f4f5f9aaec9cdbd7af84d4"
        },
        {
          "relative_path": "tests/services/test_performance_common_contract.py",
          "size_bytes": 1541,
          "sha256": "e9fe0a19748a68ef2e60cb4c2dd01d60028b33b630dffa1df4f0cd15a81b4dbd"
        },
        {
          "relative_path": "tests/services/test_sp_kpi_services.py",
          "size_bytes": 2282,
          "sha256": "6e49701bf4a8038f6cfc6ce02acee63a67eac26caafadf7a1001a139bd58424f"
        },
        {
          "relative_path": "tests/test_10_10_core_static_gate.py",
          "size_bytes": 2600,
          "sha256": "1ff395c6eece95dee42f0a9013598f6f12240a79cb9438e0cf33c4fbd51979e8"
        },
        {
          "relative_path": "tests/test_ai_analysis_excel_preview_static.py",
          "size_bytes": 1425,
          "sha256": "e8a7e35f8874a3590fb8c46551e74e0614d3e1f9018503691d79ce80c3cc0c2d"
        },
        {
          "relative_path": "tests/test_ai_executive_report_static.py",
          "size_bytes": 982,
          "sha256": "f88d7d65d5e5d7fe62e271440d9115e4bd338df3499cdcc27ef5596e55439416"
        },
        {
          "relative_path": "tests/test_ai_recommendation_priority_static.py",
          "size_bytes": 1069,
          "sha256": "76e9761fa76c126ffee6bcc6efbd1525c390c5998e433825fdc9c9abbd15af6f"
        },
        {
          "relative_path": "tests/test_ai_routes.py",
          "size_bytes": 1002,
          "sha256": "67799756de89cc3d6e6af72ea93beabd1462c64dbed7a47e903132ba2abf9b5c"
        },
        {
          "relative_path": "tests/test_claude_phase5_function_signatures.py",
          "size_bytes": 2725,
          "sha256": "c0bbf7db5c1d8af9142d9cf5bc55a7e2dfe6505bfaa693e668703c37e319c17d"
        },
        {
          "relative_path": "tests/test_claude_phase5_template_compilation.py",
          "size_bytes": 1448,
          "sha256": "e374ee77c99bad3a8de36b79094611f70f197c169c4ab96dd4e408df4fb8094b"
        },
        {
          "relative_path": "tests/test_compat_redirects.py",
          "size_bytes": 563,
          "sha256": "a358a4482d070aa7a35fa565390386f29a06e293294ab13d515363539701eae6"
        },
        {
          "relative_path": "tests/test_datetime_utils.py",
          "size_bytes": 276,
          "sha256": "16ed5aad20784973ea0c22f991fcec7a6280842e61c36c5fa32f89f113bff778"
        },
        {
          "relative_path": "tests/test_error_support.py",
          "size_bytes": 554,
          "sha256": "8e11c5d92848826019661f51a25430590cd8bba7790bb7012d967e161dc3c148"
        },
        {
          "relative_path": "tests/test_feedback_admin_endpoint_static.py",
          "size_bytes": 482,
          "sha256": "aa5ea12f8ded78f0a2b7420fef6670cd1084a9829ba04a7d296b2291601dab32"
        },
        {
          "relative_path": "tests/test_feedback_privacy_static.py",
          "size_bytes": 367,
          "sha256": "1be682e82937e9206f9fb70b26a614ce8b9ec9d06dee03a6748a7451052107cc"
        },
        {
          "relative_path": "tests/test_feedback_pulse_admin_tab_static.py",
          "size_bytes": 1140,
          "sha256": "f7425bc83f46e3fbaaee6a5578944da64a61bb3c95e3b2b079f00ded3a3d0d44"
        },
        {
          "relative_path": "tests/test_feedback_pulse_menu_visibility_static.py",
          "size_bytes": 894,
          "sha256": "870d6a296c220265a1ea78470949eb011f88ef7adc55e1555ec9fd2b12fa6546"
        },
        {
          "relative_path": "tests/test_feedback_pulse_privacy_behavior.py",
          "size_bytes": 2477,
          "sha256": "15a5dbd152ad94fe49b20ab4b7774e83e95ad6a9810e97ed63e9f0e766bdd240"
        },
        {
          "relative_path": "tests/test_hr_reports_template_no_unpack_static.py",
          "size_bytes": 540,
          "sha256": "7bc0017d521dc3f826a0da34a31fbe2fa53bb0e7678067572a742878269f616e"
        },
        {
          "relative_path": "tests/test_live_scope_and_security_static.py",
          "size_bytes": 1175,
          "sha256": "204c20a8ed7910f9e2edb0e45404c0a123811bdbb9ebd0225d90e9832a61df00"
        },
        {
          "relative_path": "tests/test_module_maturity_scoring.py",
          "size_bytes": 784,
          "sha256": "ecb3747e5e73194827c64085c8af5709fb789003733372917861543fd8f4a378"
        },
        {
          "relative_path": "tests/test_no_admin_org_units_duplicate_static.py",
          "size_bytes": 623,
          "sha256": "c0dbc2725b8ad45aa83a55d2e619e0071a60f48b3de1dea7b5d0aaad9b0cf41b"
        },
        {
          "relative_path": "tests/test_no_duplicate_admin_org_units_static.py",
          "size_bytes": 398,
          "sha256": "65ede56d3d86bd6a4018bff45ffd247d29df73f0f86e8a058e0d090f7f4f87b8"
        },
        {
          "relative_path": "tests/test_performance_archive_visibility_contract.py",
          "size_bytes": 1518,
          "sha256": "960c21c32e13123576bb9f5c763dcb847fc647540ed773ecf55e0416814e97e8"
        },
        {
          "relative_path": "tests/test_performance_chain_constitution.py",
          "size_bytes": 6350,
          "sha256": "04e84b267d33cb7ad63ebc055b110ef3bf0fda70ea2c1c62838b936dab47d65b"
        },
        {
          "relative_path": "tests/test_performance_form_guard.py",
          "size_bytes": 1056,
          "sha256": "955c5c910765b4600f90188327239082f1f724fe10eb37a0f83e1397a430091b"
        },
        {
          "relative_path": "tests/test_performance_ops_center.py",
          "size_bytes": 1314,
          "sha256": "2338ca8b88272aefce40970348d6ff9855f0ebb6b41dde409f384d64882f9fbd"
        },
        {
          "relative_path": "tests/test_performance_preflight.py",
          "size_bytes": 770,
          "sha256": "ffd5f0607f7b9a784f03f4c8a3289efc5b06b30c893c0da3def10f1aca76b92e"
        },
        {
          "relative_path": "tests/test_performance_publish_guard.py",
          "size_bytes": 1311,
          "sha256": "f7d65caf28ea89f7af72720c82840a7d14654a9e759d1eeab0d78d1baaa10624"
        },
        {
          "relative_path": "tests/test_performance_publish_preflight_static.py",
          "size_bytes": 1364,
          "sha256": "0922ad6fa805ffc1476af2d2d807c5709fe740a81f39d6e3e50f85f4c5a8a3ef"
        },
        {
          "relative_path": "tests/test_personel_analizi_dalga7_static.py",
          "size_bytes": 1046,
          "sha256": "d741893461a12400406d72d3cadb302e1403c506715ed8cded131cc406cda5b7"
        },
        {
          "relative_path": "tests/test_redis_ready_static.py",
          "size_bytes": 933,
          "sha256": "f9f4c0fd516bba0404ca8316faea9d757e07b0c7ef53426f1e41127e996488b5"
        },
        {
          "relative_path": "tests/test_shared_cache_store_behavior.py",
          "size_bytes": 651,
          "sha256": "a1bbda65c0c86f03be317f397eb9c0194ad2a4fbfcb101147d2a5fdca60daa85"
        },
        {
          "relative_path": "tests/test_sp_routes_smoke.py",
          "size_bytes": 1659,
          "sha256": "98f5f4a24ded98393aeacb8430558b7a87ea25749568101fca1256318f13a75c"
        },
        {
          "relative_path": "tests/test_team_compare_publish_visibility.py",
          "size_bytes": 948,
          "sha256": "c9e31b4037ff3f5cb2d74cf42885ce2e02b532e56ec06cb4ee51fb2280656b97"
        },
        {
          "relative_path": "tests/test_team_compare_service.py",
          "size_bytes": 3003,
          "sha256": "507c5ecfb626ee3e91d33ac35954da62e1b4447c52ae12411ca0927df85977ea"
        }
      ],
      "file_manifest_truncated": false
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_20260613_100448\\moved\\reports\\quality\\P2_BACKUP",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 208,
      "destination_test_file_count": 119,
      "destination_size_mb": 0.332
    }
  }
]
```

## Errors

```json
[]
```

## After Backup Tests

```json
{
  "backup_test_dir_count": 0,
  "backup_test_file_count": 0,
  "backup_test_dirs": []
}
```

## After Quality Backups

```json
{
  "quality_backup_dir_count": 0,
  "quality_backup_total_mb": 0,
  "quality_backup_dirs": []
}
```

## S0A Rerun

```json
{
  "returncode": 0,
  "ok": true,
  "red_flag_count": 2,
  "config_exc_bug_likely": false,
  "pytest_config_conflict_likely": false,
  "backup_test_dir_count": 0,
  "quality_backup_dir_count": 0,
  "old_venv_total_mb": 197.11,
  "pip_audit_vulnerability_count": 13
}
```

## Pytest Full Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Pytest Default Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Sonraki Adım

S0F pip-audit bağımlılık güncellemelerine geçilebilir.