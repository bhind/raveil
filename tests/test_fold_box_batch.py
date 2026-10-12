import copy,unittest
from scripts.fold_box_batch import lower,assemble,full_reference
from raveil import fold_dag as d


class BoxLoweringTests(unittest.TestCase):
    def test_rectangles_edges_wrap_and_multiple_tile_sizes(self):
        for rows,cols,tile in [(24,24,8),(24,24,16),(19,21,8),(1,1,1),(1,17,8),(17,1,8),(64,64,16)]:
            with self.subTest(rows=rows,columns=cols,tile=tile):
                words=[(0xffffffff-i*7919)&0xffffffff for i in range(rows*cols)];batch,layout=lower(words,rows,cols,tile);outputs=[]
                for item in batch['items']:
                    j=item['dag']['jobs'][0];outputs.append(dict(name=item['name'],shape=j['region']['shape'],words=d.reference(j['region'],j['inputs'])))
                self.assertEqual(assemble(outputs,layout,rows,cols),full_reference(words,rows,cols))
    def test_bad_inputs_child_limit_and_assembly_reject(self):
        for args in [([],0,1),([True],1,1),([0],True,1),([0],1,1,17),([0]*4096,64,64,8)]:
            with self.assertRaises(ValueError):lower(*args)
        batch,layout=lower([7]*4,2,2,1);outputs=[dict(name=t['name'],shape=[1,1],words=[28]) for t in layout]
        with self.assertRaises(ValueError):assemble(outputs[:-1],layout,2,2)
        changed=copy.deepcopy(layout);changed[1]['column']=0
        with self.assertRaises(ValueError):assemble(outputs,changed,2,2)

    def test_rectangle_coordinates_cannot_wrap_flat_index(self):
        _,layout=lower([7]*4,2,2,1);outputs=[dict(name=t['name'],shape=[1,1],words=[28]) for t in layout]
        for row,col in [(-1,2),(1,-2),(0,2),(2,0),(True,0)]:
            changed=copy.deepcopy(layout);changed[0].update(row=row,column=col)
            with self.subTest(row=row,column=col),self.assertRaises(ValueError):assemble(outputs,changed,2,2)
