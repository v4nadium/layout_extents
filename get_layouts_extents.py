from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsLayoutItemMap
)
from PyQt5.QtCore import QVariant

# Packages for applying style to temp layer
from qgis.core import (
    QgsFillSymbol,
    QgsSimpleLineSymbolLayer,
    QgsSingleSymbolRenderer
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

def create_layout_extents_layer(layer_name='Layouts extents', color=QColor(255, 0, 0)):
    # Get the project's CRS
    crs_project = QgsProject.instance().crs()
    project_crs_epsg = crs_project.authid()

    # Create an in-memory polygon layer using the project CRS
    vl = QgsVectorLayer('Polygon?crs=' + project_crs_epsg, 'Layouts extents', 'memory')
    pr = vl.dataProvider()

    # Define attribute fields: layout name and map item name
    pr.addAttributes([
        QgsField('layout_name', QVariant.String),
        QgsField('map_name', QVariant.String),
        QgsField('atlas_feature', QVariant.String)
    ])
    vl.updateFields()

    # Get access to the layout manager
    project = QgsProject.instance()
    layout_manager = project.layoutManager()

    # Loop over all layouts in the project
    for layout in layout_manager.layouts():
        for item in layout.items():
            if isinstance(item, QgsLayoutItemMap):
                atlas = layout.atlas()
                map_item = item  # ton QgsLayoutItemMap
                if atlas.enabled():
                    # # TODO
                    # # FIXME
                    # coverage_layer = atlas.coverageLayer()
                    # for feature in coverage_layer.getFeatures():
                    #     # Compute the page extent for this feature
                    #     extent = atlas.pageExtentForFeature(feature, map_item)  # QgsRectangle
                    #     # Convert to polygon
                    #     qgs_geom = QgsGeometry.fromPolygonXY([[
                    #         extent.topLeft(),
                    #         extent.topRight(),
                    #         extent.bottomRight(),
                    #         extent.bottomLeft(),
                    #         extent.topLeft()
                    #     ]])
                    #     feat = QgsFeature()
                    #     feat.setGeometry(qgs_geom)
                    #     feat.setAttributes([layout.name(), map_item.displayName(), feature.id()])
                    #     pr.addFeature(feat)

                    # temporary: as if no atlas
                    qpolygonf = item.visibleExtentPolygon()
                    qgs_geom = QgsGeometry.fromQPolygonF(qpolygonf)
                    feat = QgsFeature()
                    feat.setGeometry(qgs_geom)
                    feat.setAttributes([layout.name(), item.displayName(), None])
                    pr.addFeature(feat)


                else:  # Pas d'atlas : extent standard
                    qpolygonf = item.visibleExtentPolygon()
                    qgs_geom = QgsGeometry.fromQPolygonF(qpolygonf)
                    feat = QgsFeature()
                    feat.setGeometry(qgs_geom)
                    feat.setAttributes([layout.name(), item.displayName(), None])
                    pr.addFeature(feat)



                # CRS if different from the project's one
                # Get the map item CRS and the project CRS
                crs_map = item.crs()
                crs_project = project.crs()
                # Reproject the geometry if the map item's CRS differs from the project CRS
                if crs_map != crs_project:
                    tr = QgsCoordinateTransform(crs_map, crs_project, project)
                    qgs_geom.transform(tr)

                # Create and add the feature to the memory layer
                feat = QgsFeature()
                feat.setGeometry(qgs_geom)
                feat.setAttributes([layout.name(), item.displayName()])
                pr.addFeature(feat)

    # ---------------------
    # APPLY SYMBOL STYLING
    # ---------------------

    # Create an empty fill symbol (no fill)
    symbol = QgsFillSymbol.createSimple({})
    symbol.deleteSymbolLayer(0)  # Remove default fill symbol layer

    # Create a dashed line symbol layer for the outline
    outline = QgsSimpleLineSymbolLayer()
    outline.setColor(QColor(255, 0, 0))         # Red outline
    outline.setWidth(0.2)                       # Line width in mm
    outline.setPenStyle(Qt.DashLine)           # Dashed line style
    outline.setOffset(-2)                      # Offset (in mm): negative is outside the polygon

    # Add the outline symbol layer to the fill symbol
    symbol.appendSymbolLayer(outline)

    # Apply the renderer to the layer
    vl.setRenderer(QgsSingleSymbolRenderer(symbol))
    vl.triggerRepaint()

    # Finalize the layer: update extents and add it to the project
    vl.updateExtents()
    QgsProject.instance().addMapLayer(vl)

    return vl
