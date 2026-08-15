import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: collaborationStudioRoot
    width: 1024
    height: 768

    Rectangle {
        anchors.fill: parent
        color: "#181825"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Text {
                text: "Enterprise Studio Orchestration & Real-time Collaboration Platform"
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
                    text: "Active Editors Online:"
                    color: "#a6adc8"
                }

                Label {
                    id: activeEditorsCount
                    text: "3 Participants (Director, Lead Editor, Sound Supervisor)"
                    color: "#a6e3a1"
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Verify Security Audit Chain"
                    onClicked: console.log("Verifying cryptographic audit chain...")
                }

                Button {
                    text: "Export Master DCP"
                    onClicked: console.log("Exporting Digital Cinema Package...")
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#1e1e2e"
                radius: 8

                Text {
                    anchors.centerIn: parent
                    text: "QML Collaborative Studio Workspace\n[Operational Transform Sync | Multi-Engine Render Orchestration | Master DCP/MXF Export]"
                    color: "#bac2de"
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
