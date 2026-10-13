"""The dataset is fixed: no stage (and no agent) may edit, add or remove files in data/.

If this test fails, restore data/ from git rather than updating the checksums.
"""

from discovery_chef.eda.profile import data_checksums

EXPECTED_SHA256 = {
    "competitors.csv": "2ab27e9c40fcc92865b5bce61fa34930c9aed7f707f8a5135ab36e9e50e041b9",
    "idea_brief.md": "fe6375e0847993933d3f5c7b90235a1765b959da7b429180b48ddd02b42b0ddc",
    "interviews/P01.md": "fffc60012bc3349c1f65469b478711fa5640d89e43f5f0bd59de3e365b9ca35d",
    "interviews/P02.md": "c34d795c50c4945d16f9ab6a832e3477b5e528bd8ea87c7371bda8e3b6f916bf",
    "interviews/P03.md": "e994d64e9aafde81a54b7ba07404c29fb417ce3250571c9a3fb166edda8d3ef2",
    "interviews/P04.md": "96cfcb55b03cc9284d4ff56a9410f3be93dfa5a8064eeea882f4fbae87f5a1c3",
    "interviews/P05.md": "e8b09006ecc849dd0259b524ab4c0c1d1bbfd16a362a40a25c61bae35bff07e9",
    "interviews/P06.md": "b0c8345a47c26a6aa7eb7a4eae04dec757706f212172ac5ea885c471ae1c62ee",
    "interviews/P07.md": "aa3e39951c5b1632795de52a368b7793de4ca394910e4a219f4eea7a6ffbf4da",
    "interviews/P08.md": "3fec7c78f1f624a910c0a91e445f91ecc5ba7421c69ef17c871872d7470d354c",
    "interviews/P09.md": "015da0146fcf7f425e855004596673061926ee5b0f04f8a474c01e62fd325a3b",
    "interviews/P10.md": "ee4f5f72304ae1719a40981e71e64c11bbf48b40c7f4a59cbdfcf390d3d532e6",
    "market_snippets.json": "9236ebafb96bedc2ee85cd836ed8365b0493beb629bc88f71b0894d595e034b2",
}


def test_data_files_are_unchanged():
    assert data_checksums() == EXPECTED_SHA256
