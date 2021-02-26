/*$(document).ready( function(){
    // ページ読み込み時に実行したい処理
    const isbn = sessionStorage.getItem('isbn_key');
    const url = "/book_data/" + isbn + ".json";

    $.getJSON( url, function( data ) {
        if( data == null ) {
            alert("データが見つかりません");
        } else {
            if( data.画像URL == "" ){
                $("#thumbnail").html('<img src=\"\" />');
            } else {
                $("#thumbnail").html('<img src=\"' + data.画像URL + '\" style=\"border:solid 1px #000000\" />');
            }
            $("#title").text(data.タイトル);
            $("#subtitle").text(data.サブタイトル);
            $("#authors").text(data.著者);
            $("#publisher").text(data.出版社);
            $("#exp").text(data.説明)
        }
    }); 
});*/