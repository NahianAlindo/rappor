from rtlbench.extract import extract_verilog


def test_fenced_block():
    text = "Here you go:\n```verilog\nmodule a(); endmodule\n```\nDone."
    assert extract_verilog(text) == "module a(); endmodule\n"


def test_skips_non_module_fence():
    text = "```\nnot code\n```\n```systemverilog\nmodule b(); endmodule\n```"
    assert extract_verilog(text).startswith("module b")


def test_bare_module():
    assert extract_verilog("module c(); endmodule").startswith("module c")


def test_none():
    assert extract_verilog("sorry, I can't") is None
