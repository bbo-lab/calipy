import bpy
import bmesh

def getSelectionCoordinates():
    r = []
    obj = bpy.context.object
    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            if v.select:
                r.append(obj.matrix_world * v.co)
    return r
