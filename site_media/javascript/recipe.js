(function () {
    // register public actions
    $.extend(GP.actions, {
        doneAddFavoriteButton : function (invoker, data) {
            $("#addFavoriteButton").fadeOut("normal", function () {
                $("#removeFavoriteButton").fadeIn();
                GP.message("フェイバリットに追加しました。");
            });
        },

        doneRemoveFavoriteButton : function (invoker, data) {
            $("#removeFavoriteButton").fadeOut("normal", function () {
                $("#addFavoriteButton").fadeIn();
                GP.message("フェイバリットを解除しました。");
            });
        },
        
        doneVoteButton : function (invoker, data) {
            $("#voteButton").fadeOut("normal", function () {
                GP.message("このレシピに投票しました。");
            });
        },
        
        doneToggleStatus : function (invoker, data) {
            if ($.trim(invoker.text()) == "公開する") {
                invoker.html("非公開にする");
                GP.message("レシピを公開しました");
                $("#submitLi").fadeIn("normal");
                $("#openStatus").html("公開中");
            } else {
                invoker.html("公開する");
                GP.message("レシピを非公開にしました");
                $("#submitLi").fadeOut("normal");
                $("#openStatus").html("非公開");
            }
        },

        doneCopyButton : function (invoker, data) {
            $("#copyButton").fadeOut("normal", function () {
                GP.message("マイレシピに追加しました。");
            });
        }
        
    });
    
    var errorMessage = "エラーが発生しました。恐れ入りますが時間をおいてもう一度お試しください。";
    
    $(document).ready(function () {
        $("#sendMailButton").click(function () {
            var link = $(this);
            $("#mailForm").show();
            $('#mailForm').dialog({
                modal:true,
                title: "メールの送信", 
                height: 170,
                width: 440,
                draggable: false,
                resizable: false,
                overlay:{
                    opacity:0.5, 
                    background:"black"
                },
                open: function() {
                    $("#id_alter_email").attr("value", $("#id_alterEmail").attr("value"));
                    $("#id_alter_email").focus();
                },
                buttons:{
                    "送る": function() {
                        var url = link.attr("href");
                        var mail = $("#id_alter_email").attr("value");
                        var data = {alter_email:mail, csrfmiddlewaretoken: $("#usertoken").val()};
                        $.ajax({
                            url: url, 
                            data: data,
                            type: "POST",
                            success: function() {
                                GP.message(mail + " にメールを送信しました");
                            },
                            error: function() {
                                GP.message(errorMessage);
                            }
                        });
                        $(this).dialog("close");
                        $("#sendMailButton").parent().fadeOut("normal");
                    },
                    "キャンセル": function() {
                        $(this).dialog("close");
                    }
                }
            });
            return false;
        });

        $("#submitToContestButton").click(function () {
            var link = $(this);
            $("#submitForm").show();
            $('#submitForm').dialog({
                modal:true,
                title: "お題に応募", 
                height: 190,
                width: 440,
                draggable: false,
                resizable: false,
                overlay:{
                    opacity:0.5, 
                    background:"black"
                },
                buttons:{
                    "応募する": function() {
                        var url = link.attr("href");
                        var data = {contest: $("#id_contest").attr("value"),
                                    csrfmiddlewaretoken: $("#usertoken").val()};
                        $.ajax({
                            url: url, 
                            data: data, 
                            type: "POST",
                            dataType: "json",
                            success: function(data, textStatus){
                                $(".contest_name").each(function() {
                                    $(this).html(data[0].fields.name);
                                });
                                $("#editList").fadeOut("normal");
                                GP.message(data[0].fields.name + " に応募しました");
                            },
                            error: function(request, textStatus, errorThrown) {
                                alert("error");
                            }
                        });
                        link.parent().fadeOut("normal");
                        $(this).dialog("close");
                    },
                    "キャンセル": function() {
                        $(this).dialog("close");
                    }
                }
            });
            return false;
        });
        
        var deleteUrl = $("#deleteButton").attr("href");
        $("#deleteButton").attr("href", "#").click(function() {
            GP.confirm("このレシピを削除します。よろしいですか？", function() {
                $("form#generic_form")
                    .attr("action", deleteUrl)
                    .get(0).submit();
                    return false;
            });
        });
    });
})();
