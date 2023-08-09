import aiohttp
import aiofiles

from .constants import DEFAULT_API_PATH, OLD_API_PATH


# Utility methods
async def raise_for_status(response: aiohttp.ClientResponse):
    """
    Custom raise_for_status with more appropriate error message.
    """
    http_error_msg = ""

    if 400 <= response.status < 500:
        http_error_msg = "{} Client Error: {}".format(
            response.status, response.reason
        )

    elif 500 <= response.status < 600:
        http_error_msg = "{} Server Error: {}".format(
            response.status, response.reason
        )

    if http_error_msg:
        try:
            more_info: str | None = (await response.json()).get("message")
        except ValueError:
            more_info = None
        if response.reason and more_info and more_info.lower() != response.reason.lower():
            http_error_msg += ".\n\t{}".format(more_info)
        raise aiohttp.ClientResponseError(
            request_info=response.request_info,
            history=(response,),
            message=http_error_msg
        )


def clear_empty_values(args):
    """
    Scrap junk data from a dict.
    """
    result = {}
    for param in args:
        if args[param] is not None:
            result[param] = args[param]
    return result


def format_old_api_request(dataid=None, content_type=None):

    if dataid is not None:
        if content_type is not None:
            return "{}/{}.{}".format(OLD_API_PATH, dataid, content_type)
        return "{}/{}".format(OLD_API_PATH, dataid)

    if content_type is not None:
        return "{}.{}".format(OLD_API_PATH, content_type)

    raise Exception(
        "This method requires at least a dataset_id or content_type."
    )


def format_new_api_request(dataid=None, row_id=None, content_type=None):
    if dataid is not None:
        if content_type is not None:
            if row_id is not None:
                return "{}{}/{}.{}".format(
                    DEFAULT_API_PATH, dataid, row_id, content_type
                )
            return "{}{}.{}".format(DEFAULT_API_PATH, dataid, content_type)

    raise Exception("This method requires at least a dataset_id or content_type.")


def authentication_validation(username, password, access_token):
    """
    Only accept one form of authentication.
    """
    if bool(username) is not bool(password):
        raise Exception("Basic authentication requires a username AND" " password.")
    if (username and access_token) or (password and access_token):
        raise Exception(
            "Cannot use both Basic Authentication and"
            " OAuth2.0. Please use only one authentication"
            " method."
        )


async def download_file(url: str, local_filename: str) -> None:
    """
    Utility function that downloads a chunked response from the specified url to a local path.
    This method is suitable for larger downloads.
    """
    async with aiohttp.ClientSession() as session:
        response: aiohttp.ClientResponse = await session.get(url)
        async with aiofiles.open(local_filename, "wb") as outfile:
            await outfile.write(await response.read())
