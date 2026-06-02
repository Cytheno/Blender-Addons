import bpy
from bpy.props import BoolProperty
import io_scene_fbx as fbx
import mathutils

bl_info = {
    "name": "FBX Normalize Bones Export",
    "blender": (5, 0, 0),
    "category": "Export",
    "author": "Cytheno",
}

original_execute = None
original_draw = None
original_panel = None

selected_objs = None

def normalize_bones(self):
    bone_names = []
    original_bone_states = {}

    if self.use_selection:
        selected_objs = bpy.context.selected_objects
        for obj in selected_objs:
            if obj.type != 'ARMATURE':
                continue

            arm_data = obj.data

            normalize_collection = arm_data.collections.get("Normalize") or arm_data.collections.get("NormalizeBones")

            if normalize_collection:
                normalize_collection.is_visible = True

                bone_names = [bone.name for bone in normalize_collection.bones]

                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')

                for name in bone_names:
                    edit_bone = arm_data.edit_bones.get(name)
                    if edit_bone:
                        unique_key = f"{obj.name}_{name}"
                        original_bone_states[unique_key] = {
                            "matrix": edit_bone.matrix.copy(),
                            "use_connect": edit_bone.use_connect,
                            "use_inherit_rotation": edit_bone.use_inherit_rotation,
                            "use_local_location": edit_bone.use_local_location,
                            "use_relative_parent": edit_bone.use_relative_parent,
                        }

                        edit_bone.use_connect = False

                for name in bone_names:
                    edit_bone = arm_data.edit_bones.get(name)
                    if edit_bone:
                        edit_bone.use_inherit_rotation = False
                        edit_bone.use_local_location = False
                        edit_bone.use_relative_parent = False
                        edit_bone.tail = edit_bone.head + mathutils.Vector((0.0, edit_bone.length, 0.0))
                        edit_bone.roll = 0.0
            bpy.ops.object.mode_set(mode='OBJECT')
    else:
        for obj in bpy.context.scene.objects:
            if obj.type != 'ARMATURE':
                continue

            arm_data = obj.data

            normalize_collection = arm_data.collections.get("Normalize") or arm_data.collections.get("NormalizeBones")

            if normalize_collection:
                normalize_collection.is_visible = True

                bone_names = [bone.name for bone in normalize_collection.bones]

                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')

                for name in bone_names:
                    edit_bone = arm_data.edit_bones.get(name)
                    if edit_bone:
                        unique_key = f"{obj.name}_{name}"
                        original_bone_states[unique_key] = {
                            "matrix": edit_bone.matrix.copy(),
                            "use_connect": edit_bone.use_connect,
                            "use_inherit_rotation": edit_bone.use_inherit_rotation,
                            "use_local_location": edit_bone.use_local_location,
                            "use_relative_parent": edit_bone.use_relative_parent,
                        }

                        edit_bone.use_connect = False

                for name in bone_names:
                    edit_bone = arm_data.edit_bones.get(name)
                    if edit_bone:
                        edit_bone.use_inherit_rotation = False
                        edit_bone.use_local_location = False
                        edit_bone.use_relative_parent = False
                        edit_bone.tail = edit_bone.head + mathutils.Vector((0.0, edit_bone.length, 0.0))
                        edit_bone.roll = 0.0
            bpy.ops.object.mode_set(mode='OBJECT')
    
    return original_bone_states

def denormalize_bones(self,saved_bones):
    if self.use_selection:
        if not saved_bones:
            return

        selected_objs = bpy.context.selected_objects

        for obj in selected_objs:
            if obj.type != 'ARMATURE':
                continue

            arm_data = obj.data
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            for edit_bone in arm_data.edit_bones:
                unique_key = f"{obj.name}_{edit_bone.name}"
                
                if unique_key in saved_bones:
                    state = saved_bones[unique_key]
                    
                    edit_bone.use_connect = state["use_connect"]
                    edit_bone.use_inherit_rotation = state["use_inherit_rotation"]
                    edit_bone.use_local_location = state["use_local_location"]
                    edit_bone.use_relative_parent = state["use_relative_parent"]
                    
                    edit_bone.matrix = state["matrix"]

        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        if not saved_bones:
            return

        for obj in bpy.context.scene.objects:
            if obj.type != 'ARMATURE':
                continue

            arm_data = obj.data
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            for edit_bone in arm_data.edit_bones:
                unique_key = f"{obj.name}_{edit_bone.name}"
                
                if unique_key in saved_bones:
                    state = saved_bones[unique_key]
                    
                    edit_bone.use_connect = state["use_connect"]
                    edit_bone.use_inherit_rotation = state["use_inherit_rotation"]
                    edit_bone.use_local_location = state["use_local_location"]
                    edit_bone.use_relative_parent = state["use_relative_parent"]
                    
                    edit_bone.matrix = state["matrix"]
                    
        bpy.ops.object.mode_set(mode='OBJECT')

def patched_panel(layout, operator):
    header, body = layout.panel("FBX_export_armature", default_closed=True)
    header.label(text="Armature")
    if body:
        body.prop(operator, "primary_bone_axis")
        body.prop(operator, "secondary_bone_axis")
        body.prop(operator, "armature_nodetype")
        body.prop(operator, "use_armature_deform_only")
        body.prop(operator, "add_leaf_bones")
        body.prop(operator, "normalizeBones")

def patched_draw(self, context):
    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    is_file_browser = context.space_data.type == 'FILE_BROWSER'

    fbx.export_main(layout, self, is_file_browser)
    fbx.export_panel_include(layout, self, is_file_browser)
    fbx.export_panel_transform(layout, self)
    fbx.export_panel_geometry(layout, self)
    fbx.export_panel_armature(layout, self)
    fbx.export_panel_animation(layout, self)

def patched_execute(self, context):
    saved_bone_data = None

    if self.normalizeBones:
        saved_bone_data = normalize_bones(self)
        print("Finished Normalizing Bones!")

    result = original_execute(self, context)

    if self.normalizeBones and saved_bone_data:
        denormalize_bones(self,saved_bone_data)
        print("Finished DeNormalizing Bones!")

    return result

def register():
    cls = bpy.types.EXPORT_SCENE_OT_fbx

    bpy.utils.unregister_class(cls)
    cls.__annotations__['normalizeBones'] = BoolProperty(
        name="Normalize Bones",
        description="This will normalize bones from collection",
        default=False,
    )
    bpy.utils.register_class(cls)

    global original_execute, original_draw, original_panel
    original_execute = cls.execute
    original_draw = cls.draw
    original_panel = fbx.export_panel_armature

    cls.execute = patched_execute
    cls.draw = patched_draw
    fbx.export_panel_armature = patched_panel

def unregister():
    cls = bpy.types.EXPORT_SCENE_OT_fbx

    cls.execute = original_execute
    cls.draw = original_draw
    fbx.export_panel_armature = original_panel

    bpy.utils.unregister_class(cls)
    del cls.__annotations__['normalizeBones']
    bpy.utils.register_class(cls)

if __name__ == "__main__":
    register()