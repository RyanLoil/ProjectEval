function loadTable(csvPath, tableId) {
  fetch(csvPath)
    .then(res => res.text())
    .then(text => {
      const parsed = Papa.parse(text.trim(), { header: true });
      const tbody = document.querySelector(`#${tableId} tbody`);

      // 获取表头列顺序
      const headerRows = document.querySelectorAll(`#${tableId} thead tr`);
      const columnOrder = [];

      // 遍历最底层的表头（最后一行），获取列顺序
      const lastHeaderRow = headerRows[headerRows.length - 1];
      lastHeaderRow.querySelectorAll("th").forEach(th => {
        columnOrder.push(th.textContent.trim());
      });

      // 在顶部加上 Report By / Report Date / Output Format / Model
      columnOrder.unshift("Output Format");
      columnOrder.unshift("Report Date");
      columnOrder.unshift("Report By");

      parsed.data.forEach(row => {
        const tr = document.createElement("tr");
        columnOrder.forEach(col => {
          const td = document.createElement("td");
          // 检查是否为纯数字（支持小数），并转换为百分比形式
          if (!isNaN(val) && val !== "" && val !== null) {
            const num = parseFloat(val);
            // 仅对小于等于1的浮点数执行 ×100 转换
            if (num <= 1 && num >= 0) {
              val = (num * 100).toFixed(2);
            }
          }

          td.textContent = val;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    });
}

loadTable("objective.csv", "objective-table");
loadTable("execution.csv", "execution-table");

document.addEventListener("DOMContentLoaded", () => {
  const executionTable = document.querySelector("#execution-table");
  const objectiveTable = document.querySelector("#objective-table");

  new Tablesort(executionTable);
  new Tablesort(objectiveTable);

  // 默认执行表格按照 "All Avg." 降序排序（第 11 列，索引从 0 开始）
  const allAvgHeader = executionTable.querySelectorAll("thead tr")[0].querySelectorAll("th")[10];
  if (allAvgHeader) {
    allAvgHeader.click(); // 第一次点击升序
    allAvgHeader.click(); // 第二次点击降序
  }
});
