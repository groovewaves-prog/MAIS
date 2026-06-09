



// ===========================================================================
function hideColumn(class_name, val) {
    //行幅反映の為、一度行追跡機能をオフにする
    $('table.float_th').floatThead('destroy');

    if (val==false){
      $(class_name).hide();
    }else{
      $(class_name).show();
    }
};

// ===========================================================================
// アラーム検索の検索方式で 空白/非空白選択時 に検索値をdisableにする
function disable_operetor(operetor_id, operand_id ){
   if($(operetor_id).val()=="98"|$(operetor_id).val()=="99"){
        $(operand_id).prop("disabled", true);
   }else {
        $(operand_id).prop("disabled", false);
   };
};

// ===========================================================================
// 列非表示ハイライト
function highlight_on(on_select, for_select ){
         $(on_select).addClass('hightlight');
         $(for_select).addClass('hightlight');
};
function highlight_off(on_select, for_select ){
        $(on_select).removeClass('hightlight');
        $(for_select).removeClass('hightlight');
};


// ===========================================================================
function auto_comp(list, element) {

    function split( val ) {
        return val.split( /,\n*/ );
    };

    function extractLast( term ) {
        return split( term ).pop();
    };

    //複数オートコンプリート用関数生成
    mselect = function ( event, ui ) {
                var terms = split( this.value );
                terms.pop();
                terms.push( ui.item.value );
                terms.push( "" );
                this.value = terms.join( ",\n" );
                return false;
    };

    onkeydown = function( event ) {
        if ( event.keyCode === $.ui.keyCode.TAB &&
           $( this ).autocomplete( "instance" ).menu.active ) {
         event.preventDefault();
        }
    };

    afocus = function() {return false; },
    acomp_base = {autoFocus: false,
                     delay: 0,          //即時
                     minLength: 1,      //１文字入力したら
                     select: mselect,   //複数オートコンプリート
                     focus: afocus};    //複数オートコンプリート用オートフォーカスオフ


    //値渡しでauto complete用設定の連想配列をコピー
    var acomp_settings = $.extend(true, {}, acomp_base);
    //auto completeのソースのリストを指定
    acomp_settings['source'] = function( request, response ) { response( $.ui.autocomplete.filter(list, extractLast( request.term ) ) ); };
    //イベントへ追加
    $( element ).on( "keydown", onkeydown).autocomplete(acomp_settings);

};

// ===========================================================================
function all_checking(class_name, checked) {
    if(checked) {
        $("." + class_name).prop('checked', true);
    } else {
        $("." + class_name).prop('checked', false);
    }
};


// ===========================================================================
function init_slide(slide_btn_txt, slide_box, now_state_element){

  toggle_speed = 50; //msec
  close_txt    = "▲閉じる"
  open_txt     = "▼開く"

  var opened = $(now_state_element).val();
  if (opened==0 && opened != ""){
    text = $(slide_btn_txt).text().replace(close_txt, open_txt)
    $(slide_box).css('display','none');
  }else{
    text = $(slide_btn_txt).text().replace(open_txt, close_txt);;
    $(slide_box).css('display','block');
  }
  $(slide_btn_txt).text(text);
};

// ===========================================================================
function do_slide(slide_btn_txt, slide_box, now_state_element){

  toggle_speed = 50; //msec
  close_txt    = "▲閉じる"
  open_txt     = "▼開く"

  $('table.float_th').floatThead('destroy');  //テーブルヘッダ固定化機能を解除する

  var opened = $(now_state_element).val();

  if (opened==0){
    text = $(slide_btn_txt).text().replace(open_txt, close_txt)
    val=1;
  }else{
    text = $(slide_btn_txt).text().replace(close_txt, open_txt);
    val=0;
  }
  $(slide_btn_txt).text(text);
  $(now_state_element).val(val);
  $(slide_box).slideToggle(toggle_speed);

  change_url("filter_form_opened", val);
};

// ===========================================================================
// 自動リフレッシュのチェックをクリックしたとき呼ばれる
function do_refresh(auto_refresh, refresh) {
  // チェックオンの時、setTimerを呼び出してカウントダウン処理
  if ($(auto_refresh).prop("checked")) {
    val = 1;
    setTimer();
  } else {
    // チェックオフのとき、deleteTimerを呼びだす
    val = 0;
    deleteTimer();
  }
  // URLの末尾の値、reflesh=の値をvalで指定
  $(refresh).val(val);
  change_url("refresh", val);
};

// ===========================================================================
function change_url(key, value){
  var url = location.href;
  var regexp = new RegExp(key + "=(\\w|\\d)+");

  if (url.match(regexp)) {
    window.history.pushState(null, null, url.replace(regexp, key + "=" + value));
  } else {
    window.history.pushState(null, null, url + ((url.indexOf("?") == -1) ? "?" : "&") + key + "=" + value);
  }
};

// ===========================================================================
function get_query_value(key){
  var s = location.search.replace("?",""),
    query = {},
    queries = s.split("&"),
    i = 0;

    if(!s) return null;

    for(1; i < queries.length; i ++) {
      var t = queries[i].split("=");
      query[t[0]] = t[1];
    }

    return (query[key] ? query[key] : null);
};

// ===========================================================================
function del_text(element_id){
   $('#' + element_id).val('');
};

// ===========================================================================
function del_select(element_id, selected ){
   $('#' + element_id).val(selected);
};

// ===========================================================================
function openWindowSelect(cuurent_url, table_name, feald_name, input_name) {
    l = 60; // 表示するx座標
    t = 30; // 表示するy座標
    w = (screen.width) / 4; // 横幅
    h = (screen.height) / 2; // 縦幅
    x = (screen.width - w) / 2;
    y = (screen.height - h) / 2;
    // alert(controller + table_name + feald_name);
    // window.open('gw-rules/select_customer', 'select_customer', 'left=' + x ',width=500, height=700,resizable=yes');return false;
    // alert(controller + '/select/' + table_name + '/' + feald_name);
    // alert(input_name);
    if (input_name) {
      window.open(cuurent_url + '/select/' + table_name + '/' + feald_name + '/' + input_name, feald_name, "screenX=" + x + ",screenY="+y+",left="+x+",top="+y+",width="+w+",height="+ h + ",scrollbars=1");
    }else{
      window.open(cuurent_url + '/select/' + table_name + '/' + feald_name, feald_name, "screenX=" + x + ",screenY="+y+",left="+x+",top="+y+",width="+w+",height="+ h + ",scrollbars=1");
    }

    return false;
}

// ===========================================================================
function openWindowSelectConds(cuurent_url, table_name, feald_name, input_name) {
    l = 60; // 表示するx座標
    t = 30; // 表示するy座標
    w = (screen.width) / 4; // 横幅
    h = (screen.height) / 2; // 縦幅
    x = (screen.width - w) / 2;
    y = (screen.height - h) / 2;
    conds = $("#customer_name").val() + "," + $("#hostname").val() + "," + $("#ci_name").val();
    if (input_name) {
      window.open(cuurent_url + '/selectConds/' + table_name + '/' + feald_name + '/' + conds + '/' + input_name, feald_name, "screenX=" + x + ",screenY="+y+",left="+x+",top="+y+",width="+w+",height="+ h + ",scrollbars=1");
    }else{
      window.open(cuurent_url + '/selectConds/' + table_name + '/' + feald_name + '/' + conds, feald_name, "screenX=" + x + ",screenY="+y+",left="+x+",top="+y+",width="+w+",height="+ h + ",scrollbars=1");
    }

    return false;
}

// ===========================================================================
function openWindowKisys(kisys_url) {
    alert(kisys_url);
    // w = (screen.width) / 4; // 横幅
    // h = (screen.height) / 2; // 縦幅
    // x = (screen.width - w) / 2;
    // y = (screen.height - h) / 2;
    // window.open(kisys_url, "kisys_url", "screenX=" + x + ",screenY="+y+",left="+x+",top="+y+",width="+w+",height="+ h + ",scrollbars=1");
    window.open(kisys_url, "kisys_url");

    return false;
}

// ===========================================================================
function restore_check_boxs(id_prefix, to_check, array_update_ids){

    for (var variable in array_update_ids) {
      $(id_prefix + array_update_ids[variable]).prop('checked', true);
    }

}

// ===========================================================================
function count_strings(count_id, output_id){
  var count = $(count_id).val().length;
  $(output_id).text(count);
}

// ===========================================================================
/*
 * [openWindowCMDBInfo]
 * CMDB情報画面を表示する
 * @param  customer_ci 顧客略称
 */
function openWindowCMDBInfo(customer_ci) {
    l = 60; // 表示するx座標
    t = 30; // 表示するy座標
    w = (screen.width) / 2; // 横幅
    h = (screen.height) / 2; // 縦幅
    x = (screen.width - w) / 2;
    y = (screen.height - h) / 2;
    // CMDB情報画面を表示
    window.open("/baogw/gw-events/open-cmdb-info/" + customer_ci, "cmdb-info", "screenX=" + x + ",screenY="+y+",left="+x+",top="+y+",width="+w+",height="+ h + ",scrollbars=1");
}

// ===========================================================================
/*
 * [openWindowCMDB]
 * 顧客名、ホスト名及び個別監視装置名リンク押下時、CMDB情報を取得し、CMDB画面及びCMDB情報画面を表示する
 * CMDB情報を取得出来ない場合はエラーアラートを表示させる
 * @param  link_name   リンク名
 * @param  customer_ci 顧客略称
 * @param  hostname    ホスト名
 */
function openWindowCMDB(cmdb_url, link_name, customer_ci, hostname) {
    console.log(customer_ci);
    $.ajax({
        url: "/baogw/gw-events/get-cmdb-info",
        type: "POST",
        data: {"customer_ci" : customer_ci, "hostname" : hostname},
        //dataType: "json",
        async: false,
        success : function(response, data){
           console.log(response);
           console.log(customer_name);
           console.log(hostname);
           //alert(JSON.stringify(response));
            if (link_name == "device" && response.project_id) {
                // 個別監視装置名リンク押下でCMDB情報取得が出来た場合、CMDB情報画面を表示
                openWindowCMDBInfo(customer_ci)
            } else if (link_name == "hostname" && response.machine_id) {
                // ホスト名リンク押下でCMDB情報取得が出来た場合、CMDBの画面を表示
                window.open(cmdb_url + "/machine/detail/" + response.machine_id)
            } else if (link_name == "customer_name" && response.project_id) {
                // 顧客名リンク押下でCMDB情報取得が出来た場合、プロジェクト情報画面を表示
                window.open(cmdb_url + "/project/showframe/" + response.project_id)
            } else {
                // CMDB情報を取得出来ない場合、エラーアラートを表示
                alert('CMDBに登録がありません。')
            }
        },
        error: function(XMLHttpRequest, testStatus, errorThrown){
            // エラーの場合、エラーアラートを表示
            alert('ページが存在しない可能性があります。');
            console.log("XMLHttpRequest : " + XMLHttpRequest.status);
            console.log("testStatus :" + testStatus);
            console.log("errorThrown :" + errorThrown.message);
        }
    });
}

// ===========================================================================
/*
 * [openWindowDelayedEvents]
 * delayed対象一覧画面を表示する
 */
function openWindowDelayedEvents() {
  // delayed対象一覧画面を表示
  window.open("/baogw/gw-events/open-delayed-events/", "delayed-events", 'scrollbars=1');
}
