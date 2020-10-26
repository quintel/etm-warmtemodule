from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from PyQt5.QtCore import QVariant
import processing


def add_layer_as_reprojected_gpkg(project_folder, geo_layer_folder, source_file, target_crs, identifier, layer_name=''):

    path = project_folder + geo_layer_folder

    layer = QgsVectorLayer(path + source_file, '', 'ogr')

    QgsVectorFileWriter.writeAsVectorFormat(layer, '{}{}.gpkg'.format(path, identifier), 'utf-8', QgsCoordinateReferenceSystem(target_crs), 'GPKG')

    return iface.addVectorLayer('{}{}.gpkg'.format(path, identifier), layer_name, 'ogr')


def rename_attributes(layer, rename_dict):
    layer.startEditing()

    for field in layer.fields():
        if field.name() in rename_dict.keys():
            index = layer.fields().lookupField(field.name())
            layer.renameAttribute(index, rename_dict[field.name()])

    layer.commitChanges()

def add_unique_id(layer, attribute_name, prefix):

    layer.startEditing()
    layer.dataProvider().addAttributes(
                [QgsField(attribute_name, QVariant.String)])
    layer.updateFields()

    count = 1

    print('Adding IDs to: {}'.format(layer.sourceName()))

    for f in layer.getFeatures():

        f[attribute_name] = '{}{:04d}'.format(prefix, count)
        count += 1

        layer.updateFeature(f)

    layer.commitChanges()

    print('Added IDs to {} features'.format(count - 1))


def delete_all_attributes_except(array, layer):

    index = []

    print('Deleting attributes for: {}'.format(layer.sourceName()))

    layer.updateFields()

    for field in layer.fields():
        if field.name() not in array:
            index.append(layer.fields().indexFromName(field.name()))
    layer.startEditing()
    # Delete all attributes in index except the first element (mandatory 'fid' attribute)
    layer.dataProvider().deleteAttributes(index[1:])

    layer.commitChanges()

    print('Deleted {} attributes'.format(len(index)))


def export_to_csv(layer, project_folder, output_folder, output_file):

    QgsVectorFileWriter.writeAsVectorFormat(layer, project_folder + output_folder + output_file, 'utf-8', layer.crs(), 'CSV')
