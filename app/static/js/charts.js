// Personal Finance Advisor Bot - Interactive Financial Charts via Chart.js

function initFinancialDashboardCharts(chartData) {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js not loaded.");
    return;
  }

  const currencySymbol = chartData.currencySymbol || "$";
  const defaultColors = [
    "#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#64748b"
  ];

  // 1. Chart: Income vs Expense
  const ctxIncExp = document.getElementById("chartIncomeVsExpense");
  if (ctxIncExp && chartData.incomeVsExpense) {
    new Chart(ctxIncExp, {
      type: "bar",
      data: {
        labels: ["Income", "Expenses", "Savings"],
        datasets: [{
          data: [
            chartData.incomeVsExpense.income || 0,
            chartData.incomeVsExpense.expense || 0,
            chartData.incomeVsExpense.savings || 0
          ],
          backgroundColor: ["#10b981", "#ef4444", "#2563eb"],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${currencySymbol}${ctx.parsed.y.toLocaleString()}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (val) => currencySymbol + val.toLocaleString() }
          }
        }
      }
    });
  }

  // 2. Chart: Expense by Category
  const ctxCat = document.getElementById("chartCategoryExpenses");
  if (ctxCat && chartData.categoryExpenses) {
    const catLabels = chartData.categoryExpenses.labels || [];
    const catValues = chartData.categoryExpenses.values || [];

    new Chart(ctxCat, {
      type: "doughnut",
      data: {
        labels: catLabels.length ? catLabels : ["No Expenses"],
        datasets: [{
          data: catValues.length ? catValues : [1],
          backgroundColor: catLabels.length ? defaultColors.slice(0, catLabels.length) : ["#e2e8f0"],
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${currencySymbol}${ctx.parsed.toLocaleString()}`
            }
          }
        },
        cutout: "68%"
      }
    });
  }

  // 3. Chart: Monthly Spending Trend (Last 6 Months)
  const ctxTrend = document.getElementById("chartMonthlyTrend");
  if (ctxTrend && chartData.monthlyTrend) {
    new Chart(ctxTrend, {
      type: "line",
      data: {
        labels: chartData.monthlyTrend.labels || [],
        datasets: [
          {
            label: "Income",
            data: chartData.monthlyTrend.income || [],
            borderColor: "#10b981",
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            tension: 0.35,
            fill: true
          },
          {
            label: "Expenses",
            data: chartData.monthlyTrend.expenses || [],
            borderColor: "#ef4444",
            backgroundColor: "rgba(239, 68, 68, 0.05)",
            tension: 0.35,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${currencySymbol}${ctx.parsed.y.toLocaleString()}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (val) => currencySymbol + val.toLocaleString() }
          }
        }
      }
    });
  }

  // 4. Chart: Savings Growth
  const ctxSavings = document.getElementById("chartSavingsGrowth");
  if (ctxSavings && chartData.savingsGrowth) {
    new Chart(ctxSavings, {
      type: "line",
      data: {
        labels: chartData.savingsGrowth.labels || ["Start"],
        datasets: [{
          label: "Cumulative Savings",
          data: chartData.savingsGrowth.values || [0],
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.12)",
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Savings: ${currencySymbol}${ctx.parsed.y.toLocaleString()}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (val) => currencySymbol + val.toLocaleString() }
          }
        }
      }
    });
  }

  // 5. Chart: Budget vs Actual Spending
  const ctxBudget = document.getElementById("chartBudgetVsActual");
  if (ctxBudget && chartData.budgetVsActual) {
    new Chart(ctxBudget, {
      type: "bar",
      data: {
        labels: chartData.budgetVsActual.labels || [],
        datasets: [
          {
            label: "Budget Limit",
            data: chartData.budgetVsActual.budgeted || [],
            backgroundColor: "#94a3b8",
            borderRadius: 4
          },
          {
            label: "Actual Spent",
            data: chartData.budgetVsActual.spent || [],
            backgroundColor: "#2563eb",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${currencySymbol}${ctx.parsed.y.toLocaleString()}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (val) => currencySymbol + val.toLocaleString() }
          }
        }
      }
    });
  }

  // 6. Chart: Financial Goal Progress
  const ctxGoals = document.getElementById("chartGoalProgress");
  if (ctxGoals && chartData.goalProgress) {
    new Chart(ctxGoals, {
      type: "bar",
      indexAxis: "y",
      data: {
        labels: chartData.goalProgress.labels || [],
        datasets: [
          {
            label: "Saved So Far",
            data: chartData.goalProgress.current || [],
            backgroundColor: "#10b981",
            borderRadius: 4
          },
          {
            label: "Remaining to Target",
            data: chartData.goalProgress.remaining || [],
            backgroundColor: "#e2e8f0",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
            ticks: { callback: (val) => currencySymbol + val.toLocaleString() }
          },
          y: {
            stacked: true
          }
        },
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${currencySymbol}${ctx.parsed.x.toLocaleString()}`
            }
          }
        }
      }
    });
  }
}
