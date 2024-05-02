from nbt import nbt
import os
from glm import ivec2, ivec3
from gdpc import __url__, Editor, Block
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
        # self.nbt_file = nbt.NBTFile(os.path.join("nbtData", file_path))
        # self.size = self.nbt_file['size']
        # self.entities = self.nbt_file['entities']
        # self.blocks = self.nbt_file['blocks']
        # self.palette = self.nbt_file['palette']

    def blockFromPallet(self, file_path, block):
        palette = nbt.NBTFile(file_path)["palette"]
        return palette[block["state"].value]

    def get_block(self, file_path, pos: ivec3):
        blocks = nbt.NBTFile(file_path)["blocks"]
        for current_block in blocks:
            x, y, z = current_block["pos"]
            if x.value == pos.x and y.value == pos.y and z.value == pos.z:
                return Block.fromBlockStateTag(
                    self.blockFromPallet(file_path, current_block)
                )

    def get_door_pos(self, file_path):
        blocks = nbt.NBTFile(file_path)["blocks"]

        direction_map = {
            "north": (0, 0, 1),
            "east": (-1, 0, 0),
            "south": (0, 0, -1),
            "west": (1, 0, 0),
        }

        door_positions = []
        for current_block in blocks:
            block_name = self.blockFromPallet(file_path, current_block)["Name"]
            if "_door" in block_name:
                # North: +z, East: -x, South: -z, West: +x
                direction = self.blockFromPallet(file_path, current_block)["Properties"]['facing'].value
                x = current_block["pos"][0].value
                y = current_block["pos"][1].value
                z = current_block["pos"][2].value
                door_positions.append((ivec3(x, y, z), ivec3(x, y, z) + direction_map.get(direction)))
        
        if door_positions is not None:
            return door_positions
        
        return None, None

    def get_data(self, file_path, data_type: str):
        """
        Get data of building based on the nbt file.
        datatypes include: size, entities, blocks, palette
        """
        if data_type not in {"size", "entities", "blocks", "palette"}:
            raise ValueError(
                "Invalid data_type. Allowed values are 'size', 'entities', 'blocks', 'palette'"
            )

        nbt_file = nbt.NBTFile(file_path)
        return nbt_file[data_type]

    def create(self, file_path, pos: ivec3):
        data = nbt.NBTFile(file_path)
        placeStructure(structureData=data, position=pos)


if __name__ == "__main__":
    test = nbt_reader()
    block = ivec3(-211, -60, -34)
    test.get_door_pos("nbtData/basic/oak.nbt")
    print(test.get_data("nbtData/basic/oak.nbt", "size"))
    print(test.get_data("nbtData/basic/oak.nbt", "blocks"))
    print(test.get_data("nbtData/basic/oak.nbt", "palette"))
