(function () {
    // register public actions
    $.extend(GP.actions, {
        doneDeleteDirection : function (invoker, data) {
            invoker.parent(".directionData").fadeOut("normal", function () {
                $(this).remove();
            });
        }
    });
    
    var errorMessage = "エラーが発生しました。恐れ入りますが時間をおいてもう一度お試しください。";
    
    // local actions
    function wrapEditDirectionLink() {
        var url = $(this).attr("href");
        $(this).attr("href", "#");
        $(this).click(function() {
            $(".directionInput").blur(); // all input blur forcely.
            var li = $(this).parent("li.directionData");
            var label = li.children(".directionText")
            label.hide();
            li.children(".directionInput").show().focus().blur(function() {
                if ($(this).val() != label.text()) {
                    label.html($(this).val());
                    $.ajax({
                        url: url, 
                        type: "POST",
                        data: {text: $(this).val(), 
                               csrfmiddlewaretoken: $("#usertoken").val()},
                        error: function() {
                            GP.message(errorMessage);
                        }
                   });
                }
                label.show();
                $(this).hide();
            });
            return false;
        });
    }
        
    function clickAddIngredientRowsLink () {
        addIngredientRows(5);
        return false;
    }
    
    function save () {
        $("#mainForm")[0].submit();
    }
    
    // direction form functions
    function successSubmitDirectionForm (data) {
        var direction = data.direction;
        var text = direction["fields"]["text"];
        var elm = createDirectionDataElement(direction);
        elm.attr("id", "direction_" + direction["pk"]);
        elm.hide();
        $("#directionList").append(elm);
        elm.fadeIn();
    }

    function createDirectionDataElement (direction) {
        var elm = $("<li />");
        elm.addClass("directionData");
        
        var editDummyUrl = $("#editDirectionUrl").val();
        var editUrl = editDummyUrl.replace("direction_id", direction.pk);
        var editLink = $('<a/>');
        editLink.html('<img class="img01" src="/site_media/images/common/btn_edit.gif" />');
        editLink.attr("href", editUrl);
        elm.append(editLink);
        
        var deleteDummyUrl = $("#deleteDirectionUrl").attr("value");
        var deleteUrl = deleteDummyUrl.replace("direction_id", direction.pk);
        var deleteLink = $('<a/>');
        deleteLink.html('<img class="img01" src="/site_media/images/common/btn_delete.gif" />');
        deleteLink.attr("href", deleteUrl);
        deleteLink.ajaxLink(GP.actions.doneDeleteDirection);
        elm.append(deleteLink);
        
        if (direction.fields.photo != "") {
            var photo = $("<img />").attr("src", direction.fields.photo);
            elm.append(photo);
        }
        
        var textSpan = $("<span />").addClass("directionText");
        textSpan.html(direction.fields.text);
        elm.append(textSpan);
        
        var input = $('<textarea />').addClass("directionInput")
            .attr("cols", "50").attr("rows", 2)
            .text(direction.fields.text).hide();
        input.css('display', 'none');
        elm.append(input);
        
        $.each(editLink, wrapEditDirectionLink);
        
        return elm;
    }
    
    function addIngredientRows (number) {
        for (var i = 0; i < number; i++) {
            var table = $("#ingredientTable");
            var row = $('<li class="ingredientRow">素材: <input type="text" name="food" /> ... ' +
                        '分量: <input type="text" name="quantity" />' +
                        '</li>');
            row.hide();
            table.append(row);
            row.fadeIn();
        }
    }
    
    function deleteIngredient() {
        var row = $(this).parents("li.ingredientRow")[0]
        $(row).fadeOut("normal", function() {
            $(row).remove();
        });
        return false;
    }
        
    $(document).ready(function() {
        $(".saveButton").click(save);
        $(".addIngredientRowsLink").click(clickAddIngredientRowsLink);
        $(".deleteIngredientLink").click(deleteIngredient);
        $(".editDirectionLink").each(wrapEditDirectionLink);
        
        // enable ajax form.
        $("#directionForm").ajaxForm({
            dataType : "json",
            resetForm : true,
            beforeSubmit : function(data, form, options) {
                return ($.trim($("#id_text").val()) != "");
            },
            success : successSubmitDirectionForm,
            error: function (xml, status, e) {
                GP.message(errorMessage);
            }
        });
        
        // enable sorting ingredients.
        var ingSortOption = {
            cursor : "move",
            placeholder : "holder",
            stop : function() {
                $(".ingredientTableBody").sortable("refreshPositions");
            }
        };
        $(".ingredientTableBody").sortable(ingSortOption);
        
        // enable sorting directions.
        var directionList = $("#directionList");
        var dirSortOption = {
            cursor : "move",
            placeholder : "holder",
            stop : function() {
                var listData = directionList.sortable("serialize");
                listData += "&csrfmiddlewaretoken=" + $("#usertoken").val();
                var sortDirectionsUrl = $("#sortDirectionsUrl").attr("value");
                directionList.sortable("disable");
                $.ajax({
                    url: sortDirectionsUrl, 
                    data: listData, 
                    type: "POST",
                    success: function(data, textStatus) {
                        if (textStatus == "success") {
                            directionList.sortable("enable");
                        }
                    },
                    error: function() {
                        GP.message(errorMessage);
                    }
                });
            }
        };
        directionList.sortable(dirSortOption);
    });
})();
