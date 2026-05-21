let chart = null;
let lineSeries = null;
let currentGallery = 'stockus';
let currentTimeframe = '1D';

const API_BASE_URL = ''; // 상대 경로

function initChart() {
    const container = document.getElementById('chart-container');
    container.innerHTML = '';

    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: container.clientHeight,
        layout: {
            background: { type: 'solid', color: '#ffffff' },
            textColor: '#333333'
        },
        grid: {
            vertLines: { color: '#e0e0e0' },
            horzLines: { color: '#e0e0e0' }
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal
        },
        rightPriceScale: {
            borderColor: '#cccccc'
        },
        timeScale: {
            borderColor: '#cccccc',
            timeVisible: true,
            secondsVisible: false
        }
    });

    lineSeries = chart.addLineSeries({
        color: '#49a2f6',
        lineWidth: 2,
        priceFormat: { type: 'price', precision: 4 }
    });

    loadChartData();

    window.addEventListener('resize', () => {
        chart.resize(container.clientWidth, container.clientHeight);
    });
}

async function loadChartData() {
    try {
        const url = `${API_BASE_URL}/sentiment/history?gall_id=${currentGallery}&period=1Y`;
        console.log("Requesting data from:", url);

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        console.log("Received data:", data);

        if (!data || data.length === 0) {
            returnErr();
            return;
        }

        document.getElementById('chart-error').style.display = 'none';
        renderChartData(data);

    } catch (error) {
        returnErr();
    }
}

function renderChartData(data) {
    try {
        const groupedData = {};

        // 1. 기간별(1D, 7D, 1M, 1Y) 그룹화 기준 키 생성 로직
        data.forEach(item => {
            const val = item.value !== undefined ? item.value : 0;
            const d = new Date(item.time);
            
            if (isNaN(d.getTime())) return; // 올바르지 않은 날짜 패스

            let groupKey = item.time; // 1D일 때는 기본 'YYYY-MM-DD' 그대로 사용

            if (currentTimeframe === '7D') {
                // 7일 단위 묶기: 해당 주(Week)의 일요일 날짜를 구해서 묶어줍니다.
                const day = d.getDay();
                const diff = d.getDate() - day;
                const sunday = new Date(d.setDate(diff));
                groupKey = sunday.toISOString().split('T')[0];
            } 
            else if (currentTimeframe === '1M') {
                // 한달 단위 묶기: 'YYYY-MM-01' 형태로 통일
                groupKey = `${item.time.substring(0, 7)}-01`;
            } 
            else if (currentTimeframe === '1Y') {
                // 1년 단위 묶기: 'YYYY-01-01' 형태로 통일
                groupKey = `${item.time.substring(0, 4)}-01-01`;
            }

            if (!groupedData[groupKey]) {
                groupedData[groupKey] = { sum: 0, count: 0 };
            }
            groupedData[groupKey].sum += val;
            groupedData[groupKey].count += 1;
        });

        const chartData = Object.keys(groupedData).map(timeKey => {
            return {
                time: timeKey,
                value: groupedData[timeKey].sum / groupedData[timeKey].count
            };
        });

        chartData.sort((a, b) => new Date(a.time) - new Date(b.time));
        console.log(`[${currentTimeframe}] 차트 표출 데이터:`, chartData);

        lineSeries.setData(chartData);
        chart.timeScale().fitContent();
        updateEmotionGif(chartData);
    }
    catch (error) {
        returnErr();
    }
}

function returnErr() {
    document.getElementById('chart-error').style.display = 'flex';
    const gif = document.getElementById('emotionGif');
    gif.style.display = 'none';
}

function updateEmotionGif(chartData) {
    const gif = document.getElementById('emotionGif');
    if (!chartData || chartData.length === 0) {
        gif.style.display = 'none';
        return;
    }

    const lastPoint = chartData[chartData.length - 1];
    const lastValue = lastPoint.value;

    gif.src = lastValue >= 0 ? './happy.gif' : './sad.gif';
    gif.style.display = 'block';
    gif.style.width = '150px';
    gif.style.borderRadius = '50px';
    gif.style.pointerEvents = 'none';
    gif.style.position = 'absolute';
    gif.style.right = '60px';
    gif.style.bottom = '60px';
}

function changeTopic(text, gallId) {
    const topicEl = document.getElementById('topic-select');
    topicEl.childNodes[0].textContent = text + ' ';
    currentGallery = gallId;
    loadChartData();
}

document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTimeframe = btn.dataset.tf;

        loadChartData();
    });
});

document.addEventListener('DOMContentLoaded', () => {
    initChart();
});