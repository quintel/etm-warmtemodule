from qgis.core import QgsField, QgsSpatialIndex, QgsVectorFileWriter
from PyQt5.QtCore import QVariant


def add_adjacent_features(layer, attribute_name, feature_id):

    # add new field
    layer.startEditing()
    layer.dataProvider().addAttributes(
        [QgsField(attribute_name, QVariant.String)])
    layer.updateFields()

    # Create a dictionary with all features
    layer_dict = {f.id(): f for f in layer.getFeatures()}

    # Build a spatial index
    index = QgsSpatialIndex()
    for f in layer_dict.values():
        index.insertFeature(f)

    print('Adding adjacent features to: {}'.format(layer.sourceName()))

    # Loop through all features and find the features that touch it
    for f in layer_dict.values():
        geom = f.geometry()

        # select features intersecting bounding box to speed up calculation
        intersecting_ids = index.intersects(geom.boundingBox())

        # initialise adjacent feature list
        adjacent_features = []

        for intersecting_id in intersecting_ids:
            # Look up the feature from the dictionary
            intersecting_f = layer_dict[intersecting_id]

            # For our purpose we consider a feature as 'neighbour' if it
            # touches or intersects a feature. We use the 'disjoint' predicate
            # to satisfy these conditions. So if a feature is not disjoint
            # it is a neighbour.
            if (f != intersecting_f
                    and not intersecting_f.geometry().disjoint(geom)):
                adjacent_features.append(intersecting_f[feature_id])

        f[attribute_name] = ','.join(adjacent_features)
        # Update the layer with new attribute values.
        layer.updateFeature(f)

    layer.commitChanges()


def add_overlapping_features(source_layer, overlapping_layer,
                             attribute_name, identifying_attribute,
                             area_to_point=False, prefix=''):

    # add new field
    source_layer.startEditing()
    source_layer.dataProvider().addAttributes(
        [QgsField(attribute_name, QVariant.String)])
    source_layer.updateFields()

    # create feature dict for overlapping layer
    overlapping_layer_dict = {g.id(): g for g in overlapping_layer.getFeatures()}
    spatial_index = QgsSpatialIndex()

    # create spatial index
    for f in overlapping_layer_dict.values():
        spatial_index.insertFeature(f)

    area_feature_dict = {f.id(): f for f in source_layer.getFeatures()}

    print('Adding overlapping features from {} to {}'
          .format(overlapping_layer.sourceName(), source_layer.sourceName())
          )

    for f in area_feature_dict.values():

        # In some cases we do not want to find all overlapping polygons but only one,
        # e.g when checking which municipality a neighbourhood belongs to
        # Due to tiny differences between layers, a neighbourhood at the border
        # of a municipality may have a tiny overlap with multiple adjacent municipalities
        # Reducing the neighbourhood to a point mitigates this problem
        if area_to_point is True:
            # add buffering in case feature is invalid
            geom = f.geometry().buffer(0, 0).pointOnSurface()
        else:
            geom = f.geometry().buffer(0, 0)

        # find all features intersecting the bounding box of geom. This reduces the number of features in the loop below
        overlapping_feature_ids = spatial_index.intersects(geom.boundingBox())
        overlap = []

        for id in overlapping_feature_ids:
            intersecting_feature = overlapping_layer_dict[id]

            if intersecting_feature.geometry().buffer(0, 0).intersects(geom):

                overlap.append(prefix + overlapping_layer_dict[id][identifying_attribute])

        f[attribute_name] = ','.join(overlap)

        source_layer.updateFeature(f)

    source_layer.commitChanges()


def add_coordinates(layer):

    # add new fields
    layer.startEditing()
    layer.dataProvider().addAttributes(
        [QgsField('geo_coordinate_x', QVariant.Double),
         QgsField('geo_coordinate_y', QVariant.Double)])
    layer.updateFields()

    print('Adding coordinates to: {}'.format(layer.sourceName()))

    for f in layer.getFeatures():
        point = [f.geometry().centroid().asPoint()]

        for x, y in point:
            f['geo_coordinate_x'] = x
            f['geo_coordinate_y'] = y

        layer.updateFeature(f)

    layer.commitChanges()
