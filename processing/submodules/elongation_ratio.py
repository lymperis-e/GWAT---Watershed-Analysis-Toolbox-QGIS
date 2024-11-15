from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsFeature,
)
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant
import math

try:
    import processing
except:
    from qgis import processing


class ElongationRatio(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "CHANNELS",
                "CHANNELS",
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "BASIN",
                "BASIN",
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT",
                "Longest_Flow_Path",
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=None,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Create the output fields form
        outFields = QgsFields()
        outFields.append(
            QgsField("Stream Length (Km)", QVariant.Double, len=20, prec=5)
        )
        outFields.append(
            QgsField("Elongation Ratio (Re)", QVariant.Double, len=20, prec=5)
        )

        basin = self.parameterAsVectorLayer(parameters, "BASIN", context)
        channels = self.parameterAsVectorLayer(parameters, "CHANNELS", context)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            "OUTPUT",
            context,
            outFields,
            channels.wkbType(),
            channels.sourceCrs(),
        )
        features = channels.getFeatures()

        for _, feature in enumerate(features):

            out_feat = QgsFeature(outFields)
            out_feat.setGeometry(feature.geometry())

            # Calculate Re:                                          # Re=2/Length*sqrt(Area/pi)
            b = basin.getFeature(0)
            area = (
                b.geometry().area()
            ) / 1000000  # 1m2 = 1*e-6 Km --> Turn meters to Kilometers
            longest_length = out_feat.geometry().length()

            # The formula is 2/L, where L is in Km. Because .length() is in m, the conversion is 2/(L/1000)=2000/L
            elongation_ratio = (
                (2000 / longest_length) * math.sqrt(area / math.pi)
                if longest_length != 0 and area > 0
                else 0
            )

            print("Re = " + str(elongation_ratio))

            out_feat["Stream Length (Km)"] = longest_length / 1000
            out_feat["Elongation Ratio (Re)"] = elongation_ratio
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

        results = {"OUTPUT": dest_id}
        return results

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def name(self):
        return "elongation_ratio"

    def createInstance(self):
        return ElongationRatio()

    def displayName(self):
        return self.tr("Rename Layer")

    def group(self):
        return self.tr("submodules")

    def groupId(self):
        return "submodules"

    def shortHelpString(self):
        return self.tr("Rename Layer")
