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
        palette = nbt.NBTFile(os.path.join("nbtData", file_path))['palette']
        return palette[block['state'].value]

    def get_block(self, file_path, pos: ivec3):
        blocks = nbt.NBTFile(os.path.join("nbtData", file_path))['blocks']
        for current_block in blocks:
            x, y, z = current_block['pos']
            if x.value == pos.x and y.value == pos.y and z.value == pos.z:
                return Block.fromBlockStateTag(self.blockFromPallet(file_path, current_block))

    def get_door_pos(self, file_path):
        blocks = nbt.NBTFile(os.path.join("nbtData", file_path))['blocks']
        door_positions = []
        for current_block in blocks:
            block_name = self.blockFromPallet(file_path, current_block)['Name']
            if '_door' in block_name:
                x = current_block['pos'][0].value
                y = current_block['pos'][1].value
                z = current_block['pos'][2].value
                door_positions.append(ivec3(x, y, z))
        return door_positions

    def create(self, file_path, pos: ivec3):
        nbt_file = nbt.NBTFile(os.path.join("nbtData", file_path))
        placeStructure(nbt_file, pos)
        

if __name__ == "__main__":
    test = nbt_reader()
    block = ivec3(10,-60,10)
    print(test.get_door_pos('oak.nbt'))


