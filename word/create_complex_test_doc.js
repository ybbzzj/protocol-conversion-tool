const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        AlignmentType, WidthType, BorderStyle, ShadingType, HeadingLevel, PageBreak } = require('docx');
const fs = require('fs');

// 边框样式
const border = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };

// 创建表格单元格的辅助函数
function createCell(text, width, shading = null) {
  const cellOptions = {
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ 
      children: [new TextRun({ text, size: 20 })],
      alignment: AlignmentType.CENTER
    })]
  };
  
  if (shading) {
    cellOptions.shading = { fill: shading, type: ShadingType.CLEAR };
  }
  
  return new TableCell(cellOptions);
}

// 创建表头行
function createHeaderRow(headers, columnWidths, shading = "D5E8F0") {
  return new TableRow({
    children: headers.map((header, i) => 
      createCell(header, columnWidths[i], shading)
    )
  });
}

// 创建数据行
function createDataRow(data, columnWidths) {
  return new TableRow({
    children: data.map((text, i) => 
      createCell(text, columnWidths[i])
    )
  });
}

// 创建文档内容
const allSections = [];

// ==================== 第一部分：封面 ====================
allSections.push(
  new Paragraph({ 
    text: "复杂协议测试文档",
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 400, after: 400 }
  }),
  new Paragraph({ 
    text: "——包含60+个不同类型表格的综合测试文档——",
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 }
  }),
  new Paragraph({ 
    text: "版本：V2.0",
    alignment: AlignmentType.CENTER,
    spacing: { after: 100 }
  }),
  new Paragraph({ 
    text: "日期：2026年3月9日",
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 }
  }),
  new Paragraph({ 
    children: [new PageBreak()]
  })
);

// ==================== 第二部分：目录表格（不应该被识别） ====================
allSections.push(
  new Paragraph({ 
    text: "一、目录索引",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  }),
  new Paragraph({ 
    text: "表1 文档目录（测试：无数据类型列，不应识别）",
    spacing: { before: 100, after: 100 }
  })
);

const tableDirectoryWidths = [1500, 5500, 2360];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: tableDirectoryWidths,
  rows: [
    createHeaderRow(["章节号", "章节名称", "页码"], tableDirectoryWidths),
    createDataRow(["1", "系统概述", "3"], tableDirectoryWidths),
    createDataRow(["2", "通信协议定义", "5"], tableDirectoryWidths),
    createDataRow(["3", "数据结构说明", "12"], tableDirectoryWidths),
    createDataRow(["4", "接口定义", "25"], tableDirectoryWidths),
    createDataRow(["5", "附录", "50"], tableDirectoryWidths),
  ]
}));

// 表2：签名表（不应该被识别）
allSections.push(
  new Paragraph({ 
    text: "表2 文档审批表（测试：无数据类型列，不应识别）",
    spacing: { before: 200, after: 100 }
  })
);

const tableSignWidths = [1860, 1860, 1860, 1860, 1920];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: tableSignWidths,
  rows: [
    createHeaderRow(["编写", "校对", "审核", "批准", "日期"], tableSignWidths),
    createDataRow(["张三", "李四", "王五", "赵六", "2026-03-09"], tableSignWidths),
  ]
}));

allSections.push(new Paragraph({ children: [new PageBreak()] }));

// ==================== 生成50+个各种类型的表格 ====================
// 为了确保至少50个表格，我将系统化地生成各种类型

// 表3-12：标准完整表格（10个）
const standardTables = [
  { name: "端口分配表", cols: ["序号", "信源", "信宿", "信息内容", "接收组播地址", "接收端口号", "信源系统码", "信源机器码", "信宿系统码", "信宿机器码"],
    widths: [620, 930, 930, 1240, 1240, 930, 930, 930, 930, 680] },
  { name: "消息ID定义表", cols: ["序号", "信源", "信宿", "信息内容", "消息ID"],
    widths: [1200, 2330, 2330, 2330, 1170] },
  { name: "设备状态数据结构", cols: ["序号", "参数", "数据类型", "字节数", "值域", "单位", "备注"],
    widths: [930, 1860, 1550, 930, 1550, 930, 1610] },
  { name: "控制指令数据结构", cols: ["序号", "内容", "类型", "字节", "值域", "单位", "数据处理"],
    widths: [930, 2170, 1550, 930, 1550, 930, 1300] },
  { name: "IMU测量数据结构", cols: ["序号", "数据含义", "数据类型", "字节数", "取值范围", "单位", "备注"],
    widths: [710, 1550, 1240, 710, 1550, 710, 1890] },
  { name: "导航数据结构", cols: ["序号", "名称", "数据类型", "字节数", "值域", "单位", "说明"],
    widths: [710, 1400, 1400, 710, 1700, 710, 1730] },
  { name: "传感器数据", cols: ["代号", "内容", "类型", "字节", "值域", "单位", "数据处理方法"],
    widths: [1240, 2170, 1550, 930, 1550, 930, 990] },
  { name: "电源监控数据", cols: ["序号", "参数", "数据类型", "数据长度（字节）", "值域", "单位", "备注"],
    widths: [930, 1860, 1550, 1240, 1550, 930, 1300] },
  { name: "GPS数据", cols: ["序号", "字段", "类型", "字节数", "值域", "单位", "备注"],
    widths: [930, 1860, 1550, 930, 1550, 930, 1610] },
  { name: "数字IO状态", cols: ["序号", "信号名称", "数据类型", "字节数", "值域", "说明"],
    widths: [930, 2170, 1550, 930, 1550, 1230] }
];

allSections.push(
  new Paragraph({ 
    text: "二、标准完整表格",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  })
);

for (let i = 0; i < standardTables.length; i++) {
  const tableNum = 3 + i;
  const table = standardTables[i];
  
  allSections.push(
    new Paragraph({ 
      text: `表${tableNum} ${table.name}`,
      spacing: { before: 100, after: 100 }
    })
  );
  
  const rows = [createHeaderRow(table.cols, table.widths)];
  // 添加3-5行数据
  for (let j = 0; j < 4; j++) {
    const rowData = table.cols.map((col, idx) => {
      if (col.includes("序号") || col.includes("代号")) return (j + 1).toString();
      if (col.includes("数据类型") || col.includes("类型")) {
        return ["UINTEGER-32", "FLOAT", "USHORT", "UCHAR"][j % 4];
      }
      if (col.includes("字节")) return ["4", "4", "2", "1"][j % 4];
      return `数据${j + 1}`;
    });
    rows.push(createDataRow(rowData, table.widths));
  }
  
  allSections.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: table.widths,
    rows
  }));
}

allSections.push(new Paragraph({ children: [new PageBreak()] }));

// 表13-17：残缺表格（5个）
allSections.push(
  new Paragraph({ 
    text: "三、残缺表格（缺少某些列）",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  })
);

const incompleteTables = [
  { name: "系统配置参数（缺少字节数）", cols: ["序号", "参数名称", "数据类型", "备注"],
    widths: [1240, 2480, 1860, 2790] },
  { name: "状态标志位（缺少单位）", cols: ["序号", "名称", "数据类型", "字节数", "备注"],
    widths: [930, 2170, 1550, 930, 2780] },
  { name: "简化数据定义", cols: ["参数", "数据类型", "说明"],
    widths: [2330, 2790, 3240] },
  { name: "设备参数（缺少值域）", cols: ["序号", "参数", "数据类型", "字节数", "单位", "备注"],
    widths: [930, 1860, 1550, 930, 930, 2160] },
  { name: "通信帧格式", cols: ["序号", "内容", "类型", "长度", "值域", "数据转换方法"],
    widths: [930, 1860, 1550, 930, 1860, 1230] }
];

for (let i = 0; i < incompleteTables.length; i++) {
  const tableNum = 13 + i;
  const table = incompleteTables[i];
  
  allSections.push(
    new Paragraph({ 
      text: `表${tableNum} ${table.name}`,
      spacing: { before: 100, after: 100 }
    })
  );
  
  const rows = [createHeaderRow(table.cols, table.widths)];
  for (let j = 0; j < 3; j++) {
    const rowData = table.cols.map((col, idx) => {
      if (col.includes("序号")) return (j + 1).toString();
      if (col.includes("数据类型") || col.includes("类型")) {
        return ["UINTEGER-32", "USHORT", "UCHAR"][j % 3];
      }
      if (col.includes("字节") || col.includes("长度")) return ["4", "2", "1"][j % 3];
      return `内容${j + 1}`;
    });
    rows.push(createDataRow(rowData, table.widths));
  }
  
  allSections.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: table.widths,
    rows
  }));
}

allSections.push(new Paragraph({ children: [new PageBreak()] }));

// 表18-37：批量生成测试表格（20个）
allSections.push(
  new Paragraph({ 
    text: "四、批量数据采集表格",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  })
);

const batchTables = [
  "模拟量输入", "模拟量输出", "频率测量", "计数器", "PWM输出",
  "电机控制", "编码器", "步进电机", "伺服系统", "液压系统",
  "CAN总线", "RS485通信", "以太网UDP", "SPI传输", "I2C设备",
  "GNSS定位", "IMU姿态", "气压高度", "磁力计", "光流传感器"
];

for (let i = 0; i < batchTables.length; i++) {
  const tableNum = 18 + i;
  
  allSections.push(
    new Paragraph({ 
      text: `表${tableNum} ${batchTables[i]}数据`,
      spacing: { before: 100, after: 100 }
    })
  );
  
  const tableWidths = [930, 1860, 1550, 930, 1550, 930, 1610];
  const rows = [createHeaderRow(["序号", "参数", "数据类型", "字节数", "值域", "单位", "备注"], tableWidths)];
  
  for (let j = 0; j < 4; j++) {
    rows.push(createDataRow([
      (j + 1).toString(),
      `${batchTables[i]}参数${j + 1}`,
      ["UINTEGER-32", "FLOAT", "USHORT", "UCHAR"][j % 4],
      ["4", "4", "2", "1"][j % 4],
      "0~65535",
      ["ms", "V", "A", "—"][j % 4],
      `说明${j + 1}`
    ], tableWidths));
  }
  
  allSections.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: tableWidths,
    rows
  }));
}

allSections.push(new Paragraph({ children: [new PageBreak()] }));

// 表38-42：命令和状态表格（5个）
allSections.push(
  new Paragraph({ 
    text: "五、命令和状态定义",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  })
);

// 表38：系统命令
allSections.push(
  new Paragraph({ 
    text: "表38 系统命令定义",
    spacing: { before: 100, after: 100 }
  })
);

const table38Widths = [930, 1550, 2170, 2710];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table38Widths,
  rows: [
    createHeaderRow(["命令码", "数据类型", "命令名称", "说明"], table38Widths),
    createDataRow(["0x01", "UCHAR", "系统复位", "软件复位系统"], table38Widths),
    createDataRow(["0x02", "UCHAR", "启动采集", "开始数据采集"], table38Widths),
    createDataRow(["0x03", "UCHAR", "停止采集", "停止数据采集"], table38Widths),
    createDataRow(["0xFF", "UCHAR", "自检命令", "系统自检"], table38Widths),
  ]
}));

// 表39：应答码
allSections.push(
  new Paragraph({ 
    text: "表39 命令应答码",
    spacing: { before: 200, after: 100 }
  })
);

const table39Widths = [1240, 1550, 2170, 2400];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table39Widths,
  rows: [
    createHeaderRow(["应答码", "数据类型", "含义", "描述"], table39Widths),
    createDataRow(["0x00", "UCHAR", "成功", "命令执行成功"], table39Widths),
    createDataRow(["0x01", "UCHAR", "失败", "命令执行失败"], table39Widths),
    createDataRow(["0x02", "UCHAR", "超时", "命令执行超时"], table39Widths),
  ]
}));

// 表40：状态转换表（不应识别）
allSections.push(
  new Paragraph({ 
    text: "表40 系统状态转换表（测试：无数据类型，不应识别）",
    spacing: { before: 200, after: 100 }
  })
);

const table40Widths = [1860, 1860, 1860, 1880];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table40Widths,
  rows: [
    createHeaderRow(["当前状态", "触发事件", "下一状态", "动作"], table40Widths),
    createDataRow(["初始化", "上电", "待机", "系统自检"], table40Widths),
    createDataRow(["待机", "启动命令", "运行", "开始工作"], table40Widths),
    createDataRow(["运行", "停止命令", "待机", "停止工作"], table40Widths),
  ]
}));

// 表41：基本数据类型
allSections.push(
  new Paragraph({ 
    text: "表41 基本数据类型定义",
    spacing: { before: 200, after: 100 }
  })
);

const table41Widths = [930, 1860, 1550, 930, 1550, 1540];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table41Widths,
  rows: [
    createHeaderRow(["序号", "类型名", "数据类型", "字节数", "值域", "说明"], table41Widths),
    createDataRow(["1", "无符号字节", "UCHAR", "1", "0~255", "8位无符号整数"], table41Widths),
    createDataRow(["2", "无符号短整型", "USHORT", "2", "0~65535", "16位无符号整数"], table41Widths),
    createDataRow(["3", "无符号整型", "UINTEGER-32", "4", "0~4294967295", "32位无符号整数"], table41Widths),
    createDataRow(["4", "单精度浮点", "FLOAT", "4", "±3.4E±38", "IEEE 754单精度"], table41Widths),
    createDataRow(["5", "双精度浮点", "DOUBLE", "8", "±1.7E±308", "IEEE 754双精度"], table41Widths),
  ]
}));

// 表42：复合数据类型
allSections.push(
  new Paragraph({ 
    text: "表42 复合数据类型",
    spacing: { before: 200, after: 100 }
  })
);

const table42Widths = [930, 1860, 1550, 930, 2090];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table42Widths,
  rows: [
    createHeaderRow(["序号", "参数", "数据类型", "字节数", "说明"], table42Widths),
    createDataRow(["1", "设备名称", "CHAR[32]", "32", "ASCII字符串"], table42Widths),
    createDataRow(["2", "MAC地址", "UCHAR[6]", "6", "以太网MAC地址"], table42Widths),
    createDataRow(["3", "IP地址", "UCHAR[4]", "4", "IPv4地址"], table42Widths),
  ]
}));

allSections.push(new Paragraph({ children: [new PageBreak()] }));

// 表43-52：更多测试表格（10个）
allSections.push(
  new Paragraph({ 
    text: "六、特殊格式测试表格",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  })
);

// 表43：位域定义
allSections.push(
  new Paragraph({ 
    text: "表43 系统状态字位定义",
    spacing: { before: 100, after: 100 }
  })
);

const table43Widths = [1240, 1550, 2480, 2090];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table43Widths,
  rows: [
    createHeaderRow(["字节", "位号", "状态参数", "取值说明"], table43Widths),
    createDataRow(["1", "D7", "系统就绪", "0=未就绪，1=就绪"], table43Widths),
    createDataRow(["1", "D6~D5", "工作模式", "00=待机，01=工作"], table43Widths),
    createDataRow(["2", "D7~D0", "设备状态", "每位表示一个设备状态"], table43Widths),
  ]
}));

// 表44：需转换的位域表
allSections.push(
  new Paragraph({ 
    text: "表44 控制字位域（需转换格式）",
    spacing: { before: 200, after: 100 }
  })
);

const table44Widths = [560, 840, 1120, 1400, 1400, 1400, 1640];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table44Widths,
  rows: [
    createHeaderRow(["ID", "内容", "子内容", "类型（bit）", "转换类型", "判读公式", "单位"], table44Widths),
    createDataRow(["0x9001", "控制字", "使能位", "1", "UINT8", "bit0", "—"], table44Widths),
    createDataRow(["0x9001", "控制字", "模式", "2", "UINT8", "bit2~1", "—"], table44Widths),
  ]
}));

// 表45：聚合式信息流表格
allSections.push(
  new Paragraph({ 
    text: "表45 信息流定义表",
    spacing: { before: 200, after: 100 }
  })
);

allSections.push(new Paragraph({
  text: "信息名称：数据上报消息",
  spacing: { before: 100, after: 50 }
}));

const table45WidthsInfo = [2330, 6030];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table45WidthsInfo,
  rows: [
    new TableRow({
      children: [
        createCell("信源、信宿", table45WidthsInfo[0], "D5E8F0"),
        createCell("设备A → 设备B", table45WidthsInfo[1])
      ]
    }),
    new TableRow({
      children: [
        createCell("传输周期", table45WidthsInfo[0], "D5E8F0"),
        createCell("100ms", table45WidthsInfo[1])
      ]
    }),
  ]
}));

allSections.push(new Paragraph({ text: "", spacing: { after: 50 } }));

const table45Widths = [930, 1860, 1550, 930, 1550, 930, 1610];
allSections.push(new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: table45Widths,
  rows: [
    createHeaderRow(["序号", "内容", "类型", "字节", "值域", "单位", "数据处理方法"], table45Widths),
    createDataRow(["1", "时间戳", "UINTEGER-32", "4", "0~4294967295", "ms", "LSB=1ms"], table45Widths),
    createDataRow(["2", "数据1", "FLOAT", "4", "0~1000", "单位1", "直接使用"], table45Widths),
  ]
}));

// 表46-52：最后7个测试表格
const finalTestTables = [
  "时间同步协议", "文件传输数据包", "电池管理数据",
  "温度控制参数", "压力传感器校准", "振动监测数据", "故障诊断代码"
];

for (let i = 0; i < finalTestTables.length; i++) {
  const tableNum = 46 + i;
  
  allSections.push(
    new Paragraph({ 
      text: `表${tableNum} ${finalTestTables[i]}`,
      spacing: { before: 200, after: 100 }
    })
  );
  
  const tableWidths = [930, 1860, 1550, 930, 1550, 930, 1610];
  allSections.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: tableWidths,
    rows: [
      createHeaderRow(["序号", "参数", "数据类型", "字节数", "值域", "单位", "备注"], tableWidths),
      createDataRow(["1", `${finalTestTables[i]}时间`, "UINTEGER-32", "4", "0~4294967295", "ms", "时间戳"], tableWidths),
      createDataRow(["2", `${finalTestTables[i]}值1`, "FLOAT", "4", "0~1000", "单位", "测量值1"], tableWidths),
      createDataRow(["3", `${finalTestTables[i]}值2`, "SHORT", "2", "-1000~1000", "单位", "测量值2"], tableWidths),
    ]
  }));
}

allSections.push(new Paragraph({ children: [new PageBreak()] }));

// ==================== 附录说明 ====================
allSections.push(
  new Paragraph({ 
    text: "附录",
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 }
  }),
  new Paragraph({ 
    text: "本文档包含52个表格，其中：",
    spacing: { before: 100, after: 100 }
  }),
  new Paragraph({ 
    text: "• 完整标准表格：约40个（含各种列名变体）",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "• 残缺表格（缺少某些列但应识别）：约7个",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "• 不应识别的表格（无数据类型列）：约3个",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "• 聚合式信息流表格：1个",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "• 位域定义表格：2个",
    spacing: { after: 200 }
  }),
  new Paragraph({ 
    text: "测试覆盖：",
    spacing: { before: 100, after: 100 }
  }),
  new Paragraph({ 
    text: "1. 各种列名组合（序号/代号、参数/内容/字段/名称/信号名称）",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "2. 字节数的不同表达（字节数/数据长度/长度）",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "3. 数据类型的不同表达（数据类型/类型）",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "4. 残缺表格（缺少字节数、单位、值域等列）",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "5. 极简表格（只有3列核心信息）",
    spacing: { after: 50 }
  }),
  new Paragraph({ 
    text: "6. 不应识别的表格（目录、签名表、状态转换表）",
    spacing: { after: 200 }
  }),
  new Paragraph({ 
    text: "文档结束",
    alignment: AlignmentType.CENTER,
    spacing: { before: 400 }
  })
);

// 创建文档
const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: allSections
  }]
});

// 保存文档
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("复杂协议测试文档_60表格.docx", buffer);
  console.log("文档创建成功！包含52个表格");
  console.log("- 完整标准表格：约40个");
  console.log("- 残缺表格：约7个");
  console.log("- 不应识别表格：约3个");
  console.log("- 特殊格式表格：2个");
}).catch(err => {
  console.error("创建文档失败：", err);
});
