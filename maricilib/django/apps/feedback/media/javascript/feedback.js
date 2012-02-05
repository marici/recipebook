(function () {
    $(document).ready(function () {
        $("#img_feedback").click(function () {
            var options = {
                modal:false,
                title: "ぜひご協力をお願いいたします。", 
                height: 270,
                width: 480,
                position: ["left", "bottom"];
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
                                alert(data.message);
                            },
                            error: function() {
                                alert("エラーが発生しました。申し訳ありませんが時間をおいて再度お試しください。");
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
