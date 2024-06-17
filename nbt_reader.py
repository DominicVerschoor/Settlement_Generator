from nbt import nbt
from glm import ivec3
from gdpc import __url__, Block
from gdpc.interface import placeStructure


class nbt_reader:
    def __init__(self):
        """
        Initializes the class instance.
        nbt file contains:
            size
            entities
            blocks
            palette
        """

    def blockFromPallet(self, file_path, block):
        """
        Retrieves the block data from the palette based on the block's state.

        Parameters:
        - file_path: The path to the NBT file containing the palette.
        - block: The block whose state is used to retrieve the palette entry.

        Returns:
        - The block data from the palette.
        """
        palette = nbt.NBTFile(file_path)["palette"]
        return palette[block["state"].value]

    def get_block(self, file_path, pos: ivec3):
        """
        Retrieves the block at a specific position from the NBT file.

        Parameters:
        - file_path: The path to the NBT file containing the blocks.
        - pos: The position (ivec3) of the block to retrieve.

        Returns:
        - The Block object at the specified position, or None if not found.
        """
        blocks = nbt.NBTFile(file_path)["blocks"]
        for current_block in blocks:
            x, y, z = current_block["pos"]
            if x.value == pos.x and y.value == pos.y and z.value == pos.z:
                return Block.fromBlockStateTag(
                    self.blockFromPallet(file_path, current_block)
                )

        return None

    def get_data(self, file_path, data_type: str):
        """
        Retrieves specific data of a building from an NBT file.

        Parameters:
        - file_path: The path to the NBT file containing building data.
        - data_type: The type of data to retrieve. Allowed values are 'size', 'entities', 'blocks', 'palette'.

        Returns:
        - The requested data from the NBT file.

        Raises:
        - ValueError: If an invalid data_type is provided.
        """
        if data_type not in {"size", "entities", "blocks", "palette"}:
            raise ValueError(
                "Invalid data_type. Allowed values are 'size', 'entities', 'blocks', 'palette'"
            )

        nbt_file = nbt.NBTFile(file_path)
        return nbt_file[data_type]

    def create(self, file_path, pos: ivec3):
        """
        Creates a structure based on data from an NBT file at a specified position.

        Parameters:
        - file_path: The path to the NBT file containing structure data.
        - pos: The position (ivec3) where the structure should be placed.
        """
        data = nbt.NBTFile(file_path)
        placeStructure(structureData=data, position=pos)


if __name__ == "__main__":
    test = nbt_reader()

    # test.create("nbtData/basic/testsign.nbt", ivec3(-200,-60,40))
    # print(test.get_door_pos("nbtData/basic/chest_sign.nbt"))
    # print(test.get_data("nbtData/basic/chest_sign.nbt", "size"))
    # print(test.get_data("nbtData/basic/chest_sign.nbt", "blocks"))
    # print(test.get_data("nbtData/basic/chest_sign.nbt", "entities"))
    # print(test.get_data("nbtData/basic/chest_sign.nbt", "palette"))
    print(test.get_data("nbtData/basic/chest_sign.nbt", "palette"))
