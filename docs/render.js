
function loadTable(csvPath, tableId) {
  fetch(csvPath)
    .then(res => res.text())
    .then(text => {
      const parsed = Papa.parse(text.trim(), { header: true });
      const tbody = document.querySelector(`#${tableId} tbody`);

      // 获取表头列顺序
      const headerRows = document.querySelectorAll(`#${tableId} thead tr`);

      parsed.data.forEach(row => {
        const tr = document.createElement("tr");
        Object.values(row).forEach(cell => {
          const td = document.createElement("td");
          let val = cell;
          // 检查是否为纯数字（支持小数），并转换为百分比形式
          if (!isNaN(val) && val !== "" && val !== null) {
            const num = parseFloat(val);
            // 仅对小于等于1的浮点数执行 ×100 转换
            if (num <= 1 && num >= 0) {

              val = (num * 100).toFixed(2);
              // 添加进度条属性和样式
              const color = getColorByPercent(num);
              td.setAttribute("data-progress", val);
              td.style.setProperty("--progress-color", color)
              // 兼容设置伪元素宽度用的style变量
              td.style.setProperty("--progress-width", val+"%");
            }
          }

          td.textContent = val;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    });
}

function getRealColumnIndex(th) {
  const table = th.closest("table");
  const headerRows = table.querySelectorAll("thead tr");
  const targetRow = th.parentNode; // 最后一行
  const targetRowIndex = Array.from(headerRows).indexOf(targetRow);

  let colIndex = 0;

  // 用一个二维数组模拟表头格子占用情况
  // 行数为headerRows.length，列数未知，先用100足够大
  const matrix = [];

  for(let i=0; i<headerRows.length; i++) {
    matrix[i] = [];
  }

  // 填充matrix，标记每个单元格被哪些th占用
  for(let i=0; i<headerRows.length; i++) {
    let colCursor = 0;
    const cells = headerRows[i].children;
    for(let cell of cells) {
      // 找下一个空位填充
      while(matrix[i][colCursor]) colCursor++;

      const rowspan = parseInt(cell.getAttribute("rowspan")||"1", 10);
      const colspan = parseInt(cell.getAttribute("colspan")||"1", 10);

      // 标记占用区域
      for(let r=0; r<rowspan; r++) {
        for(let c=0; c<colspan; c++) {
          matrix[i+r][colCursor+c] = cell;
        }
      }

      colCursor += colspan;
    }
  }

  // 找到目标th在最后一行的哪个位置（即它是matrix[targetRowIndex][colIndex]中哪个列）
  for(let c=0; c<matrix[targetRowIndex].length; c++) {
    if(matrix[targetRowIndex][c] === th) {
      colIndex = c;
      break;
    }
  }

  return colIndex;
}


function initializeSorting() {
  const tables = [document.querySelector("#execution-table"), document.querySelector("#objective-table")];
  tables.forEach(table => {
    if (!table) return;
    // 取最后一行表头的可排序th
    const lastHeaderRow = table.querySelector("thead tr:last-child");
    const headers = table.querySelectorAll("thead th.sortable");


    // 保存当前排序状态：哪个列，升降序
    let sortState = { index: null, asc: true };

    headers.forEach((th, i) => {
      th.style.cursor = "pointer"; // 增加提示

      th.addEventListener("click", () => {
        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr"));

        // 确定实际列索引
        // 这里注意：由于多行表头，有些列跨列，必须找到th在整行中的真实位置
        // 但这里简化：因为是最后一行，th的index即对应列索引
        // 若你的表格复杂colspan，要额外计算真实索引
        const colIndex = getRealColumnIndex(th);
        console.log(colIndex);
        // 判断升降序切换
        if (sortState.index === colIndex) {
          sortState.asc = !sortState.asc;
        } else {
          sortState.index = colIndex;
          sortState.asc = true;
        }

        // 排序函数
        rows.sort((a, b) => {
          let aText = a.children[colIndex]?.textContent.trim() ?? "";
          let bText = b.children[colIndex]?.textContent.trim() ?? "";
          // 尝试转数字
          const aNum = parseFloat(aText.replace('%', ''));
          const bNum = parseFloat(bText.replace('%', ''));

          let aVal, bVal;

          // 判断是否为有效数字且非NaN
          if (!isNaN(aNum) && !isNaN(bNum)) {
            aVal = aNum;
            bVal = bNum;
          } else {
            aVal = aText.toLowerCase();
            bVal = bText.toLowerCase();
          }

          if (aVal < bVal) return sortState.asc ? -1 : 1;
          if (aVal > bVal) return sortState.asc ? 1 : -1;
          return 0;
        });

        // 清空tbody并重新插入排序后行
        tbody.innerHTML = "";
        rows.forEach(row => tbody.appendChild(row));

        // 更新排序状态指示（简单用类名）
        headers.forEach(h => h.classList.remove("asc", "desc"));
        th.classList.add(sortState.asc ? "asc" : "desc");
      });
    });
  });
}



loadTable("objective.csv", "objective-table");
loadTable("execution.csv", "execution-table");

initializeSorting();

function getColorByPercent(pct) {
  const hue = pct * 120;
  return `hsl(${hue}, 100%, 50%)`;
}
