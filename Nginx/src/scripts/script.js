// 나중에 추가할 자바스크립트 코드 (예시)
function changeTopic(topicName, topicId) {
    // 1. 제목 문구를 바꿉니다.
    document.getElementById('topic-select').innerHTML = topicName;
    
    // 2. 그래프 내용을 바꿉니다.
    document.getElementById('graph-content').innerHTML = '[' + topicName + '의 그래프로 바뀝니다]';
    
    // 3. (나중에) 진짜 파이썬 서버에 데이터를 요청할 예정입니다.
    console.log(topicId + ' 데이터를 가져오세요!');
}