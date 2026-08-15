import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: voiceCloningStudioRoot
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
                text: "Authorized Character Voice Intelligence & Performance Studio"
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
                    text: "Active Character:"
                    color: "#a6adc8"
                }

                Label {
                    id: characterNameLabel
                    text: "Hero Actor (HERO_01)"
                    color: "#89b4fa"
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Audit Consent Record"
                    onClicked: console.log("Auditing consent record...")
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#181825"
                radius: 8

                Text {
                    anchors.centerIn: parent
                    text: "QML Voice Intelligence Studio Dashboard\n[Reference Mining | Quality Ranking | Emotion Fusion | Take Evaluation]"
                    color: "#bac2de"
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
