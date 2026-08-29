# REPRODUCE

- generated: 2026-08-29T14:32:39.538174+00:00
- git commit: 133bb60c54548a2c8dfbc73c3ecee7e669732238-dirty
- mode: slice (slice-bytes 262144)

## Machine

```json
{
  "platform": "Windows-11-10.0.22631-SP0",
  "processor": "Intel64 Family 6 Model 142 Stepping 12, GenuineIntel",
  "python": "3.13.6",
  "package_versions": {
    "python": "3.13.6",
    "gzip": "stdlib",
    "bz2": "stdlib",
    "lzma": "stdlib",
    "zlib": "stdlib",
    "numpy": "2.2.6",
    "zstandard": "0.25.0",
    "brotli": "1.2.0"
  },
  "ram_total_mib": 8025,
  "ram_avail_mib": 1098
}
```

## Steps

| step | returncode | seconds |
| --- | ---: | ---: |
| pytest + codec-equivalence | 0 | 1.48 |
| corpus downloads (best-effort) | 0 | 0.35 |
| controls | 0 | 9.09 |
| natural (slice) | 0 | 88.62 |

## Corpus manifest (SHA-256 pins)

```json
{
  "enwik8@slice262144": {
    "sha256": "0cdfd008d5327addbf5b118b4a8d616a8cc2971627727b10bfb20e97920881e7",
    "bytes": 262144,
    "source": "zip enwik8.zip prefix 262144",
    "category": "text",
    "acquisition_mode": "slice"
  },
  "sdrbench_exaalt2869440_vx.f32@slice262144": {
    "sha256": "4a7274ecf55ef46c2c9315898e87ecaa1604ba2478338046366856ad6cd872a2",
    "bytes": 262144,
    "source": "sdrbench exaalt-2869440:SDRBENCH-EXAALT-2869440/vx.f32 (11477760 B, dtype <f4) [prefix 262144]",
    "category": "scientific_f32",
    "acquisition_mode": "slice"
  },
  "sdrbench_exaalt2869440_vy.f32@slice262144": {
    "sha256": "048529c77afa1110a4c2171c4fbc89a45ea4547547d1468597081a75d08e73e7",
    "bytes": 262144,
    "source": "sdrbench exaalt-2869440:SDRBENCH-EXAALT-2869440/vy.f32 (11477760 B, dtype <f4) [prefix 262144]",
    "category": "scientific_f32",
    "acquisition_mode": "slice"
  },
  "sdrbench_exaalt2869440_vz.f32@slice262144": {
    "sha256": "97aa02f7015b4d0f17a376152e51208e1d45021d67341c1bc33e016a0f93d472",
    "bytes": 262144,
    "source": "sdrbench exaalt-2869440:SDRBENCH-EXAALT-2869440/vz.f32 (11477760 B, dtype <f4) [prefix 262144]",
    "category": "scientific_f32",
    "acquisition_mode": "slice"
  },
  "sdrbench_exaalt2869440_xx.f32@slice262144": {
    "sha256": "e606d0bd9463c442aebf3d6ba72ef2290e92d564c0b7cedc0512135244dabd83",
    "bytes": 262144,
    "source": "sdrbench exaalt-2869440:SDRBENCH-EXAALT-2869440/xx.f32 (11477760 B, dtype <f4) [prefix 262144]",
    "category": "scientific_f32",
    "acquisition_mode": "slice"
  },
  "sdrbench_exaalt2869440_yy.f32@slice262144": {
    "sha256": "faa41a228bd98532d74417ab24464a9dd7009ecdbc2d7c6c35e22d75f22b77b6",
    "bytes": 262144,
    "source": "sdrbench exaalt-2869440:SDRBENCH-EXAALT-2869440/yy.f32 (11477760 B, dtype <f4) [prefix 262144]",
    "category": "scientific_f32",
    "acquisition_mode": "slice"
  },
  "sdrbench_exaalt2869440_zz.f32@slice262144": {
    "sha256": "145a27d495fb529df112cd9422333cb07aec58147a4a7752251e439d269b1a1c",
    "bytes": 262144,
    "source": "sdrbench exaalt-2869440:SDRBENCH-EXAALT-2869440/zz.f32 (11477760 B, dtype <f4) [prefix 262144]",
    "category": "scientific_f32",
    "acquisition_mode": "slice"
  },
  "silesia_dickens@slice262144": {
    "sha256": "becc366f2948cfbaefb219df19f54b101a842737428b01c7538b871a35c3edf4",
    "bytes": 262144,
    "source": "zip silesia.zip:dickens prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_mozilla@slice262144": {
    "sha256": "1baf584ca87856e51fada5fa257864019123d57aa8b9793c097eea145ee165a6",
    "bytes": 262144,
    "source": "zip silesia.zip:mozilla prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_mr@slice262144": {
    "sha256": "288236c90013320462fbe5864774054b26334be4ee59a8bde8a9797fbc9148f7",
    "bytes": 262144,
    "source": "zip silesia.zip:mr prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_nci@slice262144": {
    "sha256": "6f129b33bdf149bcdab85d1402a4f6aa4e81c0733f5fe76bb6f82bead260759e",
    "bytes": 262144,
    "source": "zip silesia.zip:nci prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_ooffice@slice262144": {
    "sha256": "41a8f0abe06c5c9e88665870be089e57c9b065bb3c27ac838cca48bcb793cb19",
    "bytes": 262144,
    "source": "zip silesia.zip:ooffice prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_osdb@slice262144": {
    "sha256": "dfafdca22a0cc7b551554126b88105a632275c0251164b07ca47633e97d91a11",
    "bytes": 262144,
    "source": "zip silesia.zip:osdb prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_reymont@slice262144": {
    "sha256": "63949f06bead1d6e40964427389b88df91aaf71e8f908e2e40fb968db3d8f682",
    "bytes": 262144,
    "source": "zip silesia.zip:reymont prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_samba@slice262144": {
    "sha256": "21c5e99f13f8cac5e099fa4c8898831d3929b068e35cae2f1a4fa424f9804d7b",
    "bytes": 262144,
    "source": "zip silesia.zip:samba prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_sao@slice262144": {
    "sha256": "2e897282e031856af823048d977bddaf54869d43dea72ba544bec003d353db3a",
    "bytes": 262144,
    "source": "zip silesia.zip:sao prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_webster@slice262144": {
    "sha256": "357ddb5945737ae814b8e6f5eb83fb1abe2d1a4cb9d76f4104a3e258f19f2208",
    "bytes": 262144,
    "source": "zip silesia.zip:webster prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_x-ray@slice262144": {
    "sha256": "51c0a846c6cbe121f3f734d32100d60fd8bdd5b79ea9506d72608665e5fef7b1",
    "bytes": 262144,
    "source": "zip silesia.zip:x-ray prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "silesia_xml@slice262144": {
    "sha256": "f2bbde07c2061c09fa41e4d4998c07847fbcc23d4ab166ca105a7f66ac8cd37b",
    "bytes": 262144,
    "source": "zip silesia.zip:xml prefix 262144",
    "category": "silesia",
    "acquisition_mode": "slice"
  },
  "uci_household_power_text@slice262144": {
    "sha256": "9f1454454bcc7ef097b21c8a931794c89eda2df9b66a8424b176466e11535fc4",
    "bytes": 262144,
    "source": "uci household power household_power_consumption.txt (prefix 262144, 262144 B)",
    "category": "telemetry_text",
    "acquisition_mode": "slice"
  }
}
```

> Slice mode: `results/natural_slice/` rows are dev-machine feasibility
> slices, not whole-file results. The pre-registered question is settled
> only by a `--mode whole` run (docs/preregistration.md S4).
