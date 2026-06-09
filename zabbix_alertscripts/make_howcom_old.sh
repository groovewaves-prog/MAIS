#!/bin/sh

if [ -e /var/lib/baogw/howcom_old ]; then
    echo 'フラグファイル"howcom_old"は既に作成されています'
else
    touch /var/lib/baogw/howcom_old
    echo 'フラグファイル"howcom_old"を作成しました'
fi

exit 0
