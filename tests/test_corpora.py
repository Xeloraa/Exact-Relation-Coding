"""Built-in corpus generators and n_rel==0 never-worse encoding."""

from __future__ import annotations

from deductive.codecs import decode, encode_passthrough
from deductive.codecs.gf2_codec import encode_bytes_best_gf2
from deductive.datasets.corpora import make_csv_fd, make_png, make_sqlite_fd, make_zip_stored
from deductive.datasets.synthetic import mixed_noise_bits

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SQLITE_HEADER = b"SQLite format 3\x00"


def test_make_png_signature_and_gf2_roundtrip():
    png = make_png(width=8, height=8, seed=0)
    assert png.startswith(PNG_SIGNATURE)
    enc = encode_bytes_best_gf2(png, widths=(8, 16))
    assert decode(enc.data) == png


def test_make_zip_stored_roundtrip():
    z = make_zip_stored({"readme.txt": b"hello zip", "blob.bin": bytes(range(64))})
    enc = encode_bytes_best_gf2(z, widths=(8, 16))
    assert decode(enc.data) == z
    pt = encode_passthrough(z)
    assert decode(pt.data) == z


def test_make_zip_stored_deterministic():
    payload = {"readme.txt": b"hello zip", "blob.bin": bytes(range(64))}
    assert make_zip_stored(payload) == make_zip_stored(payload)
    assert make_zip_stored(payload).startswith(b"PK\x03\x04")


def test_make_csv_fd_header_and_sum_column():
    raw = make_csv_fd(n_rows=20, seed=1)
    lines = raw.decode("ascii").splitlines()
    assert lines[0] == "a,b,c"
    data_rows = [line for line in lines[1:] if line]
    assert len(data_rows) == 20
    for line in data_rows:
        a, b, c = line.split(",")
        assert int(c) == int(a) + int(b)


def test_make_sqlite_fd_header():
    db = make_sqlite_fd(n_rows=8, seed=2)
    assert db.startswith(SQLITE_HEADER)


def test_n_rel_zero_equals_passthrough_size():
    ds = mixed_noise_bits(n_rows=64, n_cols=16, seed=3)
    enc = encode_bytes_best_gf2(ds.data, widths=(8, 16))
    pt = encode_passthrough(ds.data)
    assert enc.n_relations == 0
    assert len(enc.data) == len(pt.data)
    assert decode(enc.data) == ds.data
