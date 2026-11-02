"""Convert FModel Unreal landscape height maps to 16-bit grayscale PNGs."""



import sys
from pathlib import Path

from PIL import Image


# Change these paths, then run this script directly from the IDE.
INPUT_PATH = Path(
    r"F:\blenber\SF to blend\fmodel export\FactoryGame\Content\FactoryGame\Map\GameLevel01\Persistent_Level\_Generated_\E1E1IXJH446CPIWHCCJIXST0Q\PersistentLevel\LandscapeStreamingProxy_CI1M39Z1I4IIV33FKZ3VLPCP8_508_0_4_0"
)
OUTPUT_DIR: Path | None = None  # None creates Heightmaps_Grayscale beside the input.


def convert_heightmap(source_path: Path, output_path: Path) -> None:
    """Decode Unreal's packed red/green height values into a grayscale image."""
    with Image.open(source_path) as source:
        if source.mode != "RGBA":
            raise ValueError(
                f"Expected an RGBA height map, got {source.mode}: {source_path}"
            )

        rgba = source.tobytes()
        height_pixels = bytearray(source.width * source.height * 2)
        for pixel_index in range(source.width * source.height):
            source_index = pixel_index * 4
            height = (rgba[source_index] << 8) | rgba[source_index + 1]
            destination_index = pixel_index * 2
            height_pixels[destination_index : destination_index + 2] = height.to_bytes(
                2, sys.byteorder
            )

        grayscale = Image.frombytes("I;16", source.size, bytes(height_pixels))
        grayscale.save(output_path, format="PNG")
        grayscale.close()


def main() -> None:
    input_path = INPUT_PATH.expanduser()
    if input_path.is_file():
        sources = [input_path]
        default_output_dir = input_path.parent / "Heightmaps_Grayscale"
    elif input_path.is_dir():
        sources = sorted(input_path.glob("Heightmap_*.png"))
        default_output_dir = input_path / "Heightmaps_Grayscale"
    else:
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if not sources:
        raise FileNotFoundError(f"No Heightmap_*.png files found in {input_path}")

    output_dir = (OUTPUT_DIR or default_output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    for source_path in sources:
        output_path = output_dir / source_path.name
        if output_path.exists():
            print(f"Skipping {source_path.name}, already exists: {output_path}")
            continue
        convert_heightmap(source_path, output_path)
        print(f"Converted {source_path.name} -> {output_path}")

    print(f"Converted {len(sources)} height map(s) to 16-bit grayscale.")


if __name__ == "__main__":
    main()