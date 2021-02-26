// 要素を取得
let ele_1 = document.getElementById('righttop');
let ele_2 = document.getElementById('rightbottom');
let ele_3 = document.getElementById('lefttop');
let ele_4 = document.getElementById('leftbottom');
// 現在の display プロパティの値を保持
const displayOriginal_1 = ele_1.style.display;
const displayOriginal_2 = ele_2.style.display;
const displayOriginal_3 = ele_3.style.display;
const displayOriginal_4 = ele_4.style.display;
// none に設定して非表示
ele_1.style.display = 'none';
ele_2.style.display = 'none';
ele_3.style.display = 'none';
ele_4.style.display = 'none';
// ボタンが押下されたら赤枠を表示する
var play = document.getElementById("play")
play.addEventListener("click", function(){
  ele_1.style.display = displayOriginal_1;
  ele_2.style.display = displayOriginal_2;
  ele_3.style.display = displayOriginal_3;
  ele_4.style.display = displayOriginal_4;
}, false);
var stop = document.getElementById("stop")
stop.addEventListener("click", function(){
  ele_1.style.display = 'none';
  ele_2.style.display = 'none';
  ele_3.style.display = 'none';
  ele_4.style.display = 'none';
})