/**
 * login.js - 登入頁面邏輯
 * 處理圖示選擇的視覺效果
 */

(function() {
    'use strict';

    /**
     * 高亮顯示選中的圖示
     */
    function highlightSelectedIcon(iconLabel) {
        // 移除所有圖示的選中狀態
        document.querySelectorAll('.icon-label').forEach(label => {
            label.classList.remove('selected');
        });
        
        // 為當前圖示添加選中狀態
        if (iconLabel) {
            iconLabel.classList.add('selected');
        }
    }

    /**
     * 初始化圖示選擇功能
     */
    function initIconSelection() {
        // 點擊圖示時高亮顯示
        document.addEventListener('click', function(e) {
            const iconLabel = e.target.closest('.icon-label');
            if (iconLabel) {
                highlightSelectedIcon(iconLabel);
            }
        });

        // 頁面載入時高亮已選中的圖示
        const checkedInput = document.querySelector('input[name="icon"]:checked');
        if (checkedInput) {
            const iconLabel = checkedInput.closest('.icon-label');
            highlightSelectedIcon(iconLabel);
        }
    }

    // 頁面載入完成後執行
    document.addEventListener('DOMContentLoaded', initIconSelection);

})();
