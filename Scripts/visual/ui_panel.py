import bpy
from .. maze_logic . algorithm_manager import is_algo_weaved, ALGORITHM_FROM_NAME, KruskalRandom, is_algo_incompatible
from . cell_type_manager import TRIANGLE, HEXAGON, POLAR, SQUARE


class MazeGeneratorPanel(bpy.types.Panel):
    bl_idname = "MAZE_GENERATOR_PT_MainPanel"
    bl_label = "Maze Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MG'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mg_props = scene.mg_props

        row = layout.row(align=True)
        row.scale_y = 2
        sub = row.row(align=True)
        sub.operator("maze.generate", icon='VIEW_ORTHO')
        sub.scale_x = 10.0

        sub = row.row(align=True)
        sub.prop(mg_props, 'auto_update', toggle=True, icon='FILE_REFRESH', text='')
        sub.prop(mg_props, 'auto_overwrite', toggle=True, icon='MODIFIER_ON', text='')


class WallsPanel(bpy.types.Panel):
    bl_idname = "MAZE_GENERATOR_PT_WallPanel"
    bl_label = " "
    bl_parent_id = 'MAZE_GENERATOR_PT_MainPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MG'
    # bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text='Walls', icon='SNAP_EDGE')
        try:
            wall = context.scene.objects['MG_Walls']
            self.layout.prop(wall, 'hide_viewport', text='')
            self.layout.prop(wall, 'hide_render', text='')
        except KeyError:
            pass

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mg_props = scene.mg_props

        row = layout.row(align=True)
        layout.prop(mg_props, 'wall_bevel', text='Wall Bevel', slider=True)
        row.prop(mg_props, 'wall_height')
        row.prop(mg_props, 'wall_width')
        layout.prop(mg_props, 'wall_color')
        layout.prop(mg_props, 'wall_hide', text='Auto-hide wall when insetting', toggle=True)


class ParametersPanel(bpy.types.Panel):
    bl_idname = "MAZE_GENERATOR_PT_ParametersPanel"
    bl_label = "Parameters"
    bl_parent_id = 'MAZE_GENERATOR_PT_MainPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MG'

    def draw_header(self, context):
        self.layout.label(text='', icon='PREFERENCES')

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mg_props = scene.mg_props

        cell_enum_icon = 'MESH_PLANE'
        if mg_props.cell_type == POLAR:
            cell_enum_icon = 'MESH_CIRCLE'
        elif mg_props.cell_type == TRIANGLE:
            cell_enum_icon = 'OUTLINER_OB_MESH'
        elif mg_props.cell_type == HEXAGON:
            cell_enum_icon = 'SEQ_CHROMA_SCOPE'

        layout.prop_menu_enum(mg_props, 'cell_type', icon=cell_enum_icon)
        layout.prop(mg_props, 'maze_algorithm', icon='HAND', text='Solver')

        algo_incompatibility = is_algo_incompatible(mg_props)
        if algo_incompatibility:
            layout.label(text=algo_incompatibility, icon='ERROR')

        space_enum_icon = 'MESH_PLANE'
        if mg_props.maze_space_dimension == '1':
            space_enum_icon = 'MESH_CYLINDER'
        if mg_props.maze_space_dimension == '2':
            space_enum_icon = 'GP_SELECT_STROKES'
        if mg_props.maze_space_dimension == '3':
            space_enum_icon = 'GP_SELECT_STROKES'
        if mg_props.maze_space_dimension == '4':
            space_enum_icon = 'MESH_CUBE'

        layout.prop_menu_enum(mg_props, 'maze_space_dimension', icon=space_enum_icon)

        if mg_props.cell_type == POLAR:
            layout.label(text='Only Regular available with Polar', icon='ERROR', )
        elif mg_props.maze_space_dimension in ('1', '2', '3') and mg_props.cell_type == TRIANGLE:
            layout.label(text='Needs PAIR Columns (2, 4, 6, ...)', icon='ERROR', )
        elif mg_props.maze_space_dimension == '2' and mg_props.maze_columns <= 3 * mg_props.maze_rows_or_radius:
            layout.label(text='Set Columns > 3 * Rows', icon='ERROR', )
        elif mg_props.maze_space_dimension == '3' and 2 * mg_props.maze_columns > mg_props.maze_rows_or_radius:
            layout.label(text='Set Rows > 2 * Columns', icon='ERROR', )
        elif mg_props.maze_space_dimension == '4':
            layout.label(text='Dimensions are 1 face of the cube', icon='QUESTION')
        else:
            layout.label()

        def maze_size_ui(prop_name, decrease, increase, text):
            row = layout.row(align=True)
            sub = row.row()
            sub.operator('maze.tweak_maze_size', text='', icon='REMOVE').tweak_size = decrease

            sub = row.row()
            sub.prop(mg_props, prop_name, slider=True, text=text)
            sub.scale_x = 10.0

            sub = row.row()
            sub.operator('maze.tweak_maze_size', text='', icon='ADD').tweak_size = increase
            return row

        maze_size_ui('maze_columns', [-1, 0, 0], [1, 0, 0], 'Columns').enabled = mg_props.cell_type != POLAR
        row = maze_size_ui('maze_rows_or_radius', [0, -1, 0], [0, 1, 0], 'Rows').enabled = True
        row = maze_size_ui('maze_levels', [0, 0, -1], [0, 0, 1], 'Levels').enabled = mg_props.maze_space_dimension == '0'
        row = layout.row()
        row.prop(mg_props, 'seed')
        row.prop(mg_props, 'steps', icon='MOD_DYNAMICPAINT')

        layout.prop(mg_props, 'braid_dead_ends', slider=True, text='Open Dead Ends')
        layout.prop(mg_props, 'sparse_dead_ends')

        box = layout.box()
        for setting in ALGORITHM_FROM_NAME[mg_props.maze_algorithm].settings:
            box.prop(mg_props, setting)


class CellsPanel(bpy.types.Panel):
    bl_idname = "MAZE_GENERATOR_PT_CellsPanel"
    bl_label = " "
    bl_parent_id = 'MAZE_GENERATOR_PT_MainPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MG'

    def draw_header(self, context):
        self.layout.label(text='Cells', icon='TEXTURE_DATA')
        try:
            cells = context.scene.objects['MG_Cells']
            self.layout.prop(cells, 'hide_viewport', text='')
            self.layout.prop(cells, 'hide_render', text='')
        except KeyError:
            pass

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mg_props = scene.mg_props

        box = layout.box()
        row = box.row()
        row_2 = row.row()
        if mg_props.maze_algorithm == KruskalRandom.name:
            row_2.prop(mg_props, 'maze_weave', slider=True)
        else:
            row_2.prop(mg_props, 'maze_weave_toggle', toggle=True)
        row_2.enabled = is_algo_weaved(mg_props)

        row = box.row(align=True)
        row.prop(mg_props, 'cell_inset', slider=True, text='Inset')
        row.prop(mg_props, 'cell_thickness', slider=True, text='Thickness')

        row = box.row(align=True)
        row.prop(mg_props, 'cell_contour', slider=True, text='Contour')
        row.prop(mg_props, 'cell_wireframe', slider=True, text='Wireframe', icon='MOD_DECIM')

        box.prop(mg_props, 'cell_decimate', slider=True, text='Decimate', icon='MOD_DECIM')

        row = box.row(align=True)
        row.prop(mg_props, 'cell_use_smooth', toggle=True, icon='SHADING_RENDERED', text='Shade Smooth')
        row.prop(mg_props, 'cell_subdiv', text='Subdivisions', icon='MOD_SUBSURF')

        if mg_props.cell_subdiv > 0 and mg_props.cell_contour > 0:
            box.label(text='Contour conflicts with Subdivision', icon='ERROR')
        if mg_props.cell_wireframe > 0 and mg_props.cell_contour > 0:
            box.label(text='Contour can conflict with Wireframe', icon='QUESTION')

        box = layout.box()
        box.prop(mg_props, 'paint_style')
        if mg_props.paint_style != 'DISTANCE':
            box.prop(mg_props, 'seed_color_button', text='Randomize Colors', toggle=True)
        else:
            box.prop(mg_props, 'show_only_longest_path', text='Show Longest Path')
            row = box.row(align=True)
            row.prop(mg_props, 'distance_color_start', text='Start')
            row.prop(mg_props, 'distance_color_end', text='End')
        if not mg_props.auto_overwrite:
            row = box.row()
            row.label(text="Activate Auto-Overwite to Update >>", icon='ERROR')
            row.prop(mg_props, 'auto_overwrite', toggle=True, icon='MODIFIER_ON', text='')
        box.prop(mg_props, 'hue_shift', slider=True, text='Hue Shift', )
        box.prop(mg_props, 'saturation_shift', slider=True, text='Saturation Shift')
        box.prop(mg_props, 'value_shift', slider=True, text='Value Shift', icon='COLORSET_10_VEC')


class InfoPanel(bpy.types.Panel):
    bl_idname = "MAZE_GENERATOR_PT_InfoPanel"
    bl_label = "Info"
    bl_parent_id = 'MAZE_GENERATOR_PT_MainPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MG'
    # bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text='', icon='INFO')

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mg_props = scene.mg_props
        gen_time = mg_props.generation_time
        if gen_time > 0:
            layout.label(text='Generation time : ' + str(gen_time) + ' ms', icon='TEMP')
        layout.label(text='Dead ends : ' + str(mg_props.dead_ends), icon='CON_FOLLOWPATH')
