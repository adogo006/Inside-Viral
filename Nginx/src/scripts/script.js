// ============================================================================
// InsideViral 차트 스크립트
// ============================================================================

// ----------------------------------------------------------------------------
// 전역 상태
// ----------------------------------------------------------------------------
let chart = null;
let lineSeries = null;
let currentGallery = 'us-stocks';
let currentTimeframe = '7D';

// API 기본 URL (환경에 맞게 조정)
const API_BASE_URL = '/api';

// ----------------------------------------------------------------------------
// 차트 초기화
// ----------------------------------------------------------------------------
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
            timeVisible: true
        }
    });

    lineSeries = chart.addLineSeries({
        color: '#49a2f6',
        lineWidth: 2,
        priceFormat: { type: 'price', precision: 0 }
    });

    loadChartData();

    window.addEventListener('resize', () => {
        chart.resize(container.clientWidth, container.clientHeight);
    });
}

// ----------------------------------------------------------------------------
// API에서 데이터 로드
// ----------------------------------------------------------------------------
async function loadChartData() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/sentiments?gall_id=${currentGallery}&timeframe=${currentTimeframe}`
        );

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        renderChartData(result.data);
    } catch (error) {
        console.error('데이터 로드 실패:', error);
        // 실패 시 mock 데이터로 폴백
        renderMockData();
    }
}

// ----------------------------------------------------------------------------
// 차트 데이터 렌더링
// ----------------------------------------------------------------------------
function renderChartData(data) {
    if (!data || data.length === 0) {
        renderMockData();
        return;
    }

    // 시간대별 간격 계산
    let timeInterval;
    switch (currentTimeframe) {
        case '1D': timeInterval = 3600; break;      //每小时
        case '7D': timeInterval = 86400; break;    // 매일
        case '1M': timeInterval = 86400 * 7; break; // 주간
        case '1Y': timeInterval = 86400 * 30; break;// 월간
        default: timeInterval = 86400;
    }

    const now = Math.floor(Date.now() / 1000);
    const chartData = data.map((item, i) => ({
        time: now - (data.length - i) * timeInterval,
        value: item.average_sentiment
    }));

    lineSeries.setData(chartData);
    chart.timeScale().fitContent();
    updateEmotionGif(chartData);
}

// ----------------------------------------------------------------------------
// Mock 데이터 폴백 (API 연결 전/실패 시)
// ----------------------------------------------------------------------------
function renderMockData() {
    const mockData = {
        '1D': { labels: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'], data: [72, 85, 60, 90, 78, 70, 60, 30] },
        '7D': { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], data: [65, 78, 82, 70, 88, 75, 72] },
        '1M': { labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'], data: [68, 75, 82, 78] },
        '1Y': { labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], data: [55, 62, 70, 68, 75, 82, 78, 85, 72, 68, 75, 80] }
    };

    let timeInterval;
    switch (currentTimeframe) {
        case '1D': timeInterval = 3600; break;
        case '7D': timeInterval = 86400; break;
        case '1M': timeInterval = 86400 * 7; break;
        case '1Y': timeInterval = 86400 * 30; break;
        default: timeInterval = 86400;
    }

    const dataset = mockData[currentTimeframe];
    const now = Math.floor(Date.now() / 1000);

    const chartData = dataset.data.map((value, i) => ({
        time: now - (dataset.data.length - i) * timeInterval,
        value: value
    }));

    lineSeries.setData(chartData);
    chart.timeScale().fitContent();
    updateEmotionGif(chartData);
}

// ----------------------------------------------------------------------------
// 이모션 GIF 업데이트
// ----------------------------------------------------------------------------
function updateEmotionGif(chartData) {
    const gif = document.getElementById('emotionGif');
    if (!chartData || chartData.length === 0) {
        gif.style.display = 'none';
        return;
    }

    const lastPoint = chartData[chartData.length - 1];
    const lastValue = lastPoint.value;

    gif.src = lastValue >= 75 ? './happy.gif' : './sad.gif';
    gif.style.display = 'block';
    gif.style.width = '150px';
    gif.style.borderRadius = '50px';
    gif.style.pointerEvents = 'none';
    gif.style.position = 'absolute';
    gif.style.right = '60px';
    gif.style.bottom = '60px';
}

// ----------------------------------------------------------------------------
// 줌 초기화
// ----------------------------------------------------------------------------
function resetZoom() {
    chart.timeScale().fitContent();
    const data = lineSeries.data();
    updateEmotionGif(data);
}

// ----------------------------------------------------------------------------
// 갤러리 변경
// ----------------------------------------------------------------------------
function changeTopic(text, gallId) {
    const topicEl = document.getElementById('topic-select');
    topicEl.childNodes[0].textContent = text + ' ';
    currentGallery = gallId;
    loadChartData();
}

// ----------------------------------------------------------------------------
// 이벤트 리스너 등록
// ----------------------------------------------------------------------------
document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTimeframe = btn.dataset.tf;
        loadChartData();
    });
});

// ----------------------------------------------------------------------------
// DOM 로드 완료 시 차트 초기화
// ----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initChart();
});
