(function () {
    function getStyleFunction(classes, prefix) {
        prefix = prefix || "cb_";
        for (var i in classes) {
            if (classes[i].indexOf(prefix) == 0) {
                return eval("GP.actions." + classes[i].replace(prefix, ""));
            }
        }
        if (prefix == "pre_") {
            return function(target, f){ return f() };
        } else if (prefix == "eb_") {
            return function(target, e){ 
                GP.message("エラーが発生しました。申し訳ありませんが時間をおいて再度お試しください。");
            };
        } else {
            return function(){};
        }
    }
    
    var GP = window.GP = function () {};
    $.extend(GP, {
        actions : function () {},
        message: function(text) {
            var p = $('<p/>').attr("id", "mtext").html(text);
            $("#mbox").html(p).showDown();
        },
        confirm: function(text, func, options) { // requires jquery ui
            options = $.extend({
                modal:true,
                title: "操作の確認", 
                height: 120,
                width: 440,
                draggable: false,
                resizable: false,
                overlay:{
                    opacity:0.5, 
                    background:"black"
                },
                buttons:{
                    "はい": function() {
                        $(this).dialog("close");
                        func();
                    },
                    "キャンセル": function() {
                        $(this).dialog("close");
                    }
                }
            }, options);
            $("#confirmText").html(text);
            $("#confirmForm").show().dialog(options);
        }
    });
    
    $.fn.extend({
        showDown : function() {
            return this.each(function() {
                var target = $(this);
                var scrollTop  = $(document).scrollTop();
                var screenCenter = screen.width / 2;
                target.css("top", scrollTop);
                target.css("left", screenCenter - target.width() / 2);
                target.slideDown("slow");
                setTimeout(function() {
                    target.fadeOut("slow");
                }, 4000);
            });
        },
        
        swapImage : function() {
            return this.each(function() {
                var target = $(this);
                func = function() {
                    var src = target.attr("src");
                    if (src.match(/_on.(jpg|gif|png)/)) {
                        target.attr("src", src.replace("_on", ""));
                    } else {
                        target.attr("src", src.replace(/\.(jpg|gif|png)$/, "_on.$1"));
                    }
                };
                target.mouseover(func);
                target.mouseout(func);
            });
        },
        
        defaultValue : function() {
            return this.each(function() {
                $(this).focus(function() {
                    if (this.value == this.defaultValue) {
                        this.value = "";
                    }
                });
                $(this).blur(function() {
                    if (this.value == "") {
                        this.value = this.defaultValue;
                    }
                });
            });
        },
        
        ajaxLink : function(callback, errback) {
            return this.each(function() {
                var target = $(this);
                var url = target.attr("href");
                target.attr("href", "#");
                target.click(function (){
                    var classes = target.attr("class").split(" ");
                    getStyleFunction(classes, "pre_")(target, function() {
                        data = { csrfmiddlewaretoken: $("#usertoken").val()};
                        $.ajax({
                            url: url,
                            data: data,
                            type: "POST",
                            dataType: "json",
                            success: function (data, textStatus){
                                if (textStatus == "success") {
                                    if (callback) {
                                        return callback(target, data);
                                    } else {
                                        return getStyleFunction(classes)(target, data);
                                    }
                                }
                            },
                            error: function(request, textStatus, errorThrown) {
                                if (errback) {
                                    return errback(target, errorThrown);
                                } else {
                                    return getStyleFunction(classes, "eb_")(target, errorThrown);
                                }
                            }
                        });
                    });
                    return false;
                });
            });
        }
    });
        
    $(document).ready(function () {
        // embed ajax action for links.
        $("a.ajaxLink").ajaxLink();
        $("img.swap").swapImage();
        $("#search_ipt01").defaultValue();
        function validateQuery() {
            if ($("#search_ipt01").val() == "" ||
                $("#search_ipt01").val() == $("#search_ipt01")[0].defaultValue) {
                return false;
            } else {
                return true;
            }
        }
        $("#headsubmit").click(function() {
            if (validateQuery()) $("#headsearch")[0].submit();
        });
        $("#headsearch").submit(validateQuery);
        if ($.trim($("#mtext").text()) != "") {
            $("#mbox").showDown();
        }
        
        $("#img_feedback").click(function () {
            var options = {
                modal:false,
                title: "ご意見はこちらからどうぞ。", 
                height: 220,
                width: 480,
                position: ["left", "bottom"],
                draggable: true,
                resizable: true,
                overlay:{
                    opacity:0.1, 
                    background:"white"
                },
                buttons:{
                    "送る": function() {
                        $("#form_feedback").ajaxSubmit({
                            dataType: "json",
                            clearForm: true,
                            success: function(data, textStatus) {
                                GP.message(data.message);
                            },
                            error: function() {
                                GP.message("エラーが発生しました。申し訳ありませんが時間をおいて再度お試しください。");
                            }
                        });
                        $(this).dialog("close");
                    },
                    "キャンセル": function() {
                        $(this).dialog("close");
                    }
                }
            };
            $("#div_feedback").show();
            $("#div_feedback").dialog(options);
            $("#id_feedback-text").focus();
            return false;
        });
    });
})();
