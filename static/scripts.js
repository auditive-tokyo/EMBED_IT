// Diplay Scrapy Modal Window 
function showPopup() {
    // Show the modal
    $("#myModal").modal();
}

// Save Settings
function saveSettings(tab) {
    var settings = {};
    if (tab === 'scrape_url') {
        settings = {
            url: document.querySelector('#scrape_url input[name="url"]').value,
            include_elements: document.querySelector('#scrape_url textarea[name="include_elements"]').value,
            exclude_tags: document.querySelector('#scrape_url textarea[name="exclude_tags"]').value,
            exclude_elements: document.querySelector('#scrape_url textarea[name="exclude_elements"]').value,
            output_file: document.querySelector('#scrape_url input[name="output_file"]').value,
            site_name: document.querySelector('#scrape_url input[name="site_name"]').value
        };
    } else if (tab === 'set_api_key') {
        settings = {
            api_key: document.querySelector('#set_api_key input[name="api_key"]').value,
        };
    }
    fetch('/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ [tab]: settings })
    });
}

// Load Settings
function loadSettings(tab) {
    fetch('/load_settings')
        .then(response => response.json())
        .then(allSettings => {
            var settings = allSettings[tab];
            if (tab === 'scrape_url') {
                document.querySelector('#scrape_url input[name="url"]').value = settings.url;
                document.querySelector('#scrape_url textarea[name="include_elements"]').value = settings.include_elements || '';
                document.querySelector('#scrape_url textarea[name="exclude_tags"]').value = settings.exclude_tags || '';
                document.querySelector('#scrape_url textarea[name="exclude_elements"]').value = settings.exclude_elements || '';
                document.querySelector('#scrape_url input[name="output_file"]').value = settings.output_file || '';
                document.querySelector('#scrape_url input[name="site_name"]').value = settings.site_name || '';
            } else if (tab === 'set_api_key') {
                document.querySelector('#set_api_key input[name="api_key"]').value = settings.api_key || '';
            }
        });
}

// Memorize which tab you were at
$(function () {
    // ページが読み込まれたときにローカルストレージから現在のタブを読み込む
    var currentTab = localStorage.getItem('currentTab');
    if (currentTab) {
        $('.nav-tabs a[href="' + currentTab + '"]').tab('show');
    } else {
        // ローカルストレージに現在のタブがない場合は、最初のタブを表示
        $('.nav-tabs a:first').tab('show');
    }

    // タブが切り替えられたときに現在のタブをローカルストレージに保存
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        localStorage.setItem('currentTab', $(e.target).attr('href'));
    });
});

// ソースリストを表示とシリアルキーをjsonから読み込み表示
window.onload = function () {
    // Send a GET request to the server to get the file list
    fetch('/list_files')
        .then(response => response.json())
        .then(data => {
            // Get the file list element
            var fileList = document.getElementById('file-list');

            // Clear the file list
            fileList.innerHTML = '';

            // Create a table
            var table = document.createElement('table');
            table.className = 'table'; // Add Bootstrap class

            // Add each file to the table
            data.files.forEach(file => {
                var tr = document.createElement('tr');

                // Create a cell for the file name
                var td1 = document.createElement('td');
                td1.textContent = file.replace('.csv', '');
                tr.appendChild(td1);

                // Create a cell for the show button
                var td2 = document.createElement('td');
                var showButton = document.createElement('button');
                showButton.textContent = 'Show';
                showButton.className = 'btn btn-sm btn-info'; // Add Bootstrap classes
                showButton.onclick = function () {
                    showFile(file);
                };
                td2.appendChild(showButton);
                tr.appendChild(td2);

                // Create a cell for the delete button
                var td3 = document.createElement('td');
                var deleteButton = document.createElement('button');
                deleteButton.textContent = 'Delete';
                deleteButton.className = 'btn btn-sm btn-danger'; // Add Bootstrap classes
                deleteButton.onclick = function () {
                    deleteFile(file);
                };
                td3.appendChild(deleteButton);
                tr.appendChild(td3);

                table.appendChild(tr);
            });

            fileList.appendChild(table);
        });
};

let currentEditingFile = "";  // 編集中のファイル名を保存するグローバル変数

// CSVファイルを表示
function showFile(filename) {
    currentEditingFile = filename;  // 編集中のファイル名を保存
    fetch('/get_csv_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename }),
    })
        .then(response => response.json())
        .then(data => {
            var html = '<table class="table csv-table">';
            // Add table headers
            html += '<tr>';
            html += '<th class="bg-primary text-white">title</th>';
            html += '<th class="bg-primary text-white">url</th>';
            html += '<th class="bg-primary text-white">Action</th>';
            html += '</tr>';
            html += '<tr>';
            html += '<th colspan="3" class="bg-secondary text-white">text</th>';
            html += '</tr>';
            // Add table rows
            data.forEach((row, rowIndex) => {
                html += '<tr class="data-row">';
                html += '<td><input type="text" value="' + row['title'] + '" size="30" class="form-control"></td>';
                html += '<td><input type="text" value="' + row['url'] + '" size="30" class="form-control"></td>';
                html += '<td><button onclick="deleteRow(this)" class="btn btn-danger">Delete</button></td>';
                html += '</tr>';
                html += '<tr class="data-row">';
                html += '<td colspan="3"><textarea rows="4" cols="60" class="form-control">' + row['text'] + '</textarea></td>';
                html += '</tr>';
            });
            html += '</table>';
            html += '<button onclick="saveChanges()" class="btn btn-success">Save Changes</button>';
            document.getElementById('csv-display').innerHTML = html;
        });
}

// 変更を保存
function saveChanges() {
    var table = document.querySelector('.csv-table');
    var rows = Array.from(table.querySelectorAll('.data-row'));
    var data = [];

    // Skip the header row
    for (var i = 0; i < rows.length; i += 2) {
        var titleRow = rows[i];
        var textRow = rows[i + 1];
        var rowData = {};

        var titleCell = titleRow.querySelector('input[type="text"]');
        var urlCell = titleRow.querySelectorAll('input[type="text"]')[1];
        var textCell = textRow.querySelector('textarea');

        rowData['title'] = titleCell.value;
        rowData['url'] = urlCell.value;
        rowData['text'] = textCell.value;

        data.push(rowData);
    }

    // Send the updated data to the server
    fetch('/save_edited_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data: data, filename: currentEditingFile }),  // 保存するファイル名を指定
    })
        .then(response => response.text())
        .then(text => {
            if (text === 'OK') {
                alert('Changes saved successfully.');
            } else {
                alert('Failed to save changes.');
            }
        });
}

// 行を削除する関数
function deleteRow(buttonElement) {
    var row = buttonElement.closest('.data-row');
    row.nextElementSibling.remove();  // Remove the corresponding 'text' row
    row.remove();  // Remove the 'title' and 'url' row
}

// ソースリストから削除
function deleteFile(filename) {
    // Send a POST request to the server to delete the file
    fetch('/delete_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename }),
    })
        .then(response => response.json())
        .then(data => {
            // Refresh the file list
            window.onload();
        });
}