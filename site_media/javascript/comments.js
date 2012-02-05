(function () {
    // register public actions
    $.extend(GP.actions, {
        doneApproveComment : function (invoker, data) {
            invoker.parents(".approveCommentButton").fadeOut("normal", function() {
                GP.message("コメントを承認しました。");
            });
        },
        
        doneApproveComment2 : function (invoker, data) {
            invoker.fadeOut("normal", function() {
                GP.message("コメントを承認しました。");
            });
        },
        
        doneDeleteComment : function (invoker, data) {
            var comment = invoker.parents(".comment");
            comment.prev().fadeOut(); // h2
            comment.fadeOut("normal", function() {
                GP.message("コメントを削除しました。");
            });
        },
        
        doneDeleteComment2 : function (invoker, data) {
            var comment = invoker.parents(".comment");
            comment.fadeOut("normal", function() {
                GP.message("コメントを削除しました。");
            });
        },
        
        confirmDeleteComment : function (invoker, func) {
            var comment = invoker.parents(".comment");
            var title = comment.prev().text(); // h2
            GP.confirm(title + "<br />を削除してよろしいですか？", func);
        },
        
        confirmDeleteComment2 : function(invoker, func) {
            var title = $.trim(invoker.parents(".comment").text());
            if (title.length > 50) title = title.substring(0, 50) + " ...";
            GP.confirm(title + "<br />を削除してよろしいですか？", func);
        }

    });
})();