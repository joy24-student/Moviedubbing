import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: analyticsStudioRoot
    width: 1024
    height: 768

    Rectangle {
        anchors.fill: parent
        color: "#1e1e2e"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Text {
                text: "Multi-Tenant Studio Analytics, Cloud Sync & LoRA Fine-Tuning Hub"
                color: "#cdd6f4"
                font.pixelSize: 20
                font.bold: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#45475a"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Label {
                    text: "Studio Budget Status:"
                    color: "#a6adc8"
                }

                Label {
                    id: budgetStatusLabel
                    text: "HEALTHY ($21.75 / $500.00)"
                    color: "#a6e3a1"
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Sync Project to Cloud"
                    onClicked: console.log("Triggering cloud differential sync...")
                }

                Button {
                    text: "Train LoRA Adapter"
                    onClicked: console.log("Triggering LoRA fine-tuning job...")
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#181825"
                radius: 8

                Text {
                    anchors.centerIn: parent
                    text: "QML Analytics & Cloud Sync Dashboard\n[Differential S3/GCS Sync | LoRA Adapter Fine-Tuning | Cost-per-Minute Tracking]"
                    color: "#bac2de"
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
