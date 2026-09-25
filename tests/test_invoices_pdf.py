def test_pdf_module_imports():
    import backend.pdf                        # noqa: F401
    from backend.pdf.company import COMPANY

    assert COMPANY["name"] == "JB Transports"
    assert isinstance(COMPANY["phones"], list)
    assert len(COMPANY["phones"]) == 2
