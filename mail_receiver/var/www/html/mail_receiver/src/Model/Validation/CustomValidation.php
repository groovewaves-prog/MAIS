<?php

namespace App\Model\Validation;

use Cake\Validation\Validation;

use function PHPSTORM_META\elementType;

class CustomValidation extends Validation
{
    public static function isMatchAlphaNumericAndCustomSymbol($check)
    {
        return (bool) preg_match('/^[a-zA-Z0-9!-:-@¥[-`{-~]*$/', $check);
    }

    public static function isNotMatchedControlCharacter($check)
    {
        return (bool) !preg_match('/[\x00-\x1F\x7F]/', $check);
    }
}
