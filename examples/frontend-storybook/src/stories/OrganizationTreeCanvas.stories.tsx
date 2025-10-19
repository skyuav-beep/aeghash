import type { Meta, StoryObj } from "@storybook/react";
import React, { useState } from "react";
import {
  OrganizationNode,
  OrganizationTreeCanvas
} from "../components/organization/OrganizationTreeCanvas";

const rootNode: OrganizationNode = {
  id: "root",
  name: "홍길동",
  rank: "Diamond",
  pvLeft: 128400,
  pvRight: 102900,
  status: "active",
  children: [
    {
      id: "node-1",
      name: "김서연",
      rank: "Platinum",
      pvLeft: 60210,
      pvRight: 48200,
      status: "active",
      children: [
        {
          id: "node-1-1",
          name: "이도현",
          rank: "Gold",
          pvLeft: 20210,
          pvRight: 16200,
          status: "warning"
        },
        {
          id: "node-1-2",
          name: "박하린",
          rank: "Silver",
          pvLeft: 12040,
          pvRight: 9800,
          status: "active"
        }
      ]
    },
    {
      id: "node-2",
      name: "최민준",
      rank: "Platinum",
      pvLeft: 45200,
      pvRight: 54680,
      status: "hold",
      children: [
        {
          id: "node-2-1",
          name: "정가은",
          rank: "Gold",
          pvLeft: 18200,
          pvRight: 15280,
          status: "active"
        },
        {
          id: "node-2-2",
          name: "오지후",
          rank: "Silver",
          pvLeft: 8900,
          pvRight: 10100,
          status: "active"
        }
      ]
    }
  ]
};

const meta: Meta<typeof OrganizationTreeCanvas> = {
  title: "Admin/Organization/OrganizationTreeCanvas",
  component: OrganizationTreeCanvas,
  parameters: {
    layout: "fullscreen"
  }
};

export default meta;
type Story = StoryObj<typeof OrganizationTreeCanvas>;

export const Default: Story = {
  render: () => {
    const [selectedNode, setSelectedNode] = useState<OrganizationNode | null>(null);
    return (
      <div style={{ padding: "32px", background: "#f7f7f7", minHeight: "100vh" }}>
        <OrganizationTreeCanvas
          root={rootNode}
          onSelectNode={(node) => {
            setSelectedNode(node);
          }}
        />
        <aside
          style={{
            marginTop: "24px",
            padding: "16px",
            background: "#ffffff",
            borderRadius: "12px",
            border: "1px solid #e0e0e0"
          }}
        >
          <h3 style={{ marginTop: 0 }}>선택 노드</h3>
          {selectedNode ? (
            <dl>
              <div>
                <dt>이름</dt>
                <dd>{selectedNode.name}</dd>
              </div>
              <div>
                <dt>직급</dt>
                <dd>{selectedNode.rank}</dd>
              </div>
              <div>
                <dt>좌측 PV</dt>
                <dd>{selectedNode.pvLeft.toLocaleString()}</dd>
              </div>
              <div>
                <dt>우측 PV</dt>
                <dd>{selectedNode.pvRight.toLocaleString()}</dd>
              </div>
              <div>
                <dt>상태</dt>
                <dd>{selectedNode.status}</dd>
              </div>
            </dl>
          ) : (
            <p>노드를 선택하면 상세 정보가 표시됩니다.</p>
          )}
        </aside>
      </div>
    );
  }
};

export const ZoomedOut: Story = {
  args: {
    root: rootNode,
    zoom: 0.7
  }
};
