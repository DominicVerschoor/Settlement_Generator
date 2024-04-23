from nbt import nbt
import os
from glm import ivec2, ivec3
from gdpc import __url__, Editor, Block

class nbt_reader:
    def __init__(self, file_path):
        """
        Initializes the class instance.
        nbt file contains:
            size
            entities
            blocks
            palette
        """
        self.nbt_file = nbt.NBTFile(os.path.join("nbtData", file_path))
        self.size = self.nbt_file['size']
        self.entities = self.nbt_file['entities']
        self.blocks = self.nbt_file['blocks']
        self.palette = self.nbt_file['palette']

    def blockFromPallet(self, block):
        return self.palette[block['state'].value]

    def get_block(self, pos: ivec3):
        for current_block in self.blocks:
            x, y, z = current_block['pos']
            if x.value == pos.x and y.value == pos.y and z.value == pos.z:
                return Block.fromBlockStateTag(self.blockFromPallet(current_block))

    def get_door_pos(self):
        door_positions = []
        for current_block in self.blocks:
            block_name = self.blockFromPallet(current_block)['Name']
            if '_door' in block_name:
                x = current_block['pos'][0].value
                y = current_block['pos'][1].value
                z = current_block['pos'][2].value
                door_positions.append(ivec3(x, y, z))
        return door_positions

        


if __name__ == "__main__":
    test = nbt_reader('oak.nbt')
    block = ivec3(1,2,0)
    test.paste_structure()

