from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "files"
SPRITE_DIR = ASSETS_DIR / "rewilding_sprites" / "transparent"
BACKGROUND_DIR = ASSETS_DIR / "backgrounds"
MENU_BUTTON_DIR = ASSETS_DIR / "menu_buttons"
CHARACTER_DIR = ASSETS_DIR / "characters"

ACORN = {"path": str(SPRITE_DIR / "acorn_16x16.png")}
CLAM = {"path": str(SPRITE_DIR / "clam_16x16.png")}
CORAL = {"path": str(SPRITE_DIR / "coral_32x32.png")}
CRAB = {"path": str(SPRITE_DIR / "crab_blue_32x16.png")}
FISH_ORANGE = {"path": str(SPRITE_DIR / "fish_orange_32x16.png")}
FISH_TEAL = {"path": str(SPRITE_DIR / "fish_teal_32x16.png")}
FISH_YELLOW = {"path": str(SPRITE_DIR / "fish_yellow_32x16.png")}
KELP = {"path": str(SPRITE_DIR / "kelp_16x48.png")}
ROCK = {"path": str(SPRITE_DIR / "rock_32x16.png")}
ROCKS_WITH_MUD = {"path": str(SPRITE_DIR / "rocks_with_mud_48x16.png")}
SEA_URCHIN = {"path": str(SPRITE_DIR / "sea_urchin_16x16.png")}
SHELL = {"path": str(SPRITE_DIR / "shell_16x16.png")}
SUN = {"path": str(SPRITE_DIR / "sun_32x32.png")}
TREE = {"path": str(SPRITE_DIR / "tree_32x48.png")}

MENU_BACKGROUND = {"path": str(BACKGROUND_DIR / "marker_overlay_check.png")}
PATRICK_HOUSE_BACKGROUND = {"path": str(BACKGROUND_DIR / "patrick_house_480x270_crisp.png")}
SPONGEBOB_HOUSE_BACKGROUND = {"path": str(BACKGROUND_DIR / "spongebob_house.png")}
SANDY_TREEDOME_BACKGROUND = {"path": str(BACKGROUND_DIR / "underwater_grass_field_480x270.png")}
SQUIDWARD_HOUSE_BACKGROUND = {"path": str(BACKGROUND_DIR / "squidward_house_480x270_crisp.png")}
OCTOPUS_REEF_BACKGROUND = {"path": str(BACKGROUND_DIR / "octopus_reef_scene_480x270.png")}

PATRICK_MENU_BUTTON = {"path": str(MENU_BUTTON_DIR / "patrick_landmark_56h.png")}
SANDY_MENU_BUTTON = {"path": str(MENU_BUTTON_DIR / "sandy_landmark_56h.png")}
SPONGEBOB_MENU_BUTTON = {"path": str(MENU_BUTTON_DIR / "spongebob_house_cutout_200h.png")}
SQUIDWARD_MENU_BUTTON = {"path": str(MENU_BUTTON_DIR / "squidward_home_button_56h.png")}
MR_KRABS_MENU_BUTTON = {"path": str(MENU_BUTTON_DIR / "krusty_krab_button_56h.png")}

# Frame order for every character: 1 = struggling/fixing, 2 = neutral
# default, 3 = celebrating a perfect habitat (see habitat_scene.py).
PATRICK_FRAME_1 = {"path": str(CHARACTER_DIR / "pattrick" / "patrick1_character_96h.png")}
PATRICK_FRAME_2 = {"path": str(CHARACTER_DIR / "pattrick" / "patrick2_character_96h copy.png")}
PATRICK_FRAME_3 = {"path": str(CHARACTER_DIR / "pattrick" / "patrick3_character_96h.png")}
SPONGEBOB_FRAME_1 = {"path": str(CHARACTER_DIR / "spongebob" / "spongebob_1_character_96h.png")}
SPONGEBOB_FRAME_2 = {"path": str(CHARACTER_DIR / "spongebob" / "spongebob_2_character_96h.png")}
SPONGEBOB_FRAME_3 = {"path": str(CHARACTER_DIR / "spongebob" / "spongebob_3_character_96h.png")}
SANDY_FRAME_1 = {"path": str(CHARACTER_DIR / "sandy" / "sandy_1_character_96h.png")}
SANDY_FRAME_2 = {"path": str(CHARACTER_DIR / "sandy" / "sandy2_character_96h.png")}
SANDY_FRAME_3 = {"path": str(CHARACTER_DIR / "sandy" / "sandy3_character_96h.png")}
SQUIDWARD_FRAME_1 = {"path": str(CHARACTER_DIR / "squidward" / "squidward1_character_96h copy.png")}
SQUIDWARD_FRAME_2 = {"path": str(CHARACTER_DIR / "squidward" / "squidward2_character_96h.png")}
SQUIDWARD_FRAME_3 = {"path": str(CHARACTER_DIR / "squidward" / "squidward3_character_96h.png")}
# Krabs' source files don't follow the same 1=struggling/2=neutral/3=celebrating
# order as the other characters: the art for frame slot 3 (celebrating) is
# "krabs2", and the art for frame slot 1 (struggling) is "krabs3" - matched by
# what each pose actually shows (grin+claws-up vs. anxious over a money bag),
# not by filename number.
MR_KRABS_FRAME_1 = {"path": str(CHARACTER_DIR / "krabs" / "krabs3_character_96h.png")}
MR_KRABS_FRAME_2 = {"path": str(CHARACTER_DIR / "krabs" / "krabs_character_96h.png")}
MR_KRABS_FRAME_3 = {"path": str(CHARACTER_DIR / "krabs" / "krabs2_character_fullres.png")}
