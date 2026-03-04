import { WEBUI_API_BASE_URL } from '$lib/constants';

// 获取 Episode 列表
export const getEpisodes = async (token: string, skip = 0, limit = 30) => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/episodes/?skip=${skip}&limit=${limit}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取单个 Episode
export const getEpisodeById = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/episodes/${id}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 创建 Episode
export const createEpisode = async (token: string, episode: object) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/episodes/`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(episode)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 更新 Episode
export const updateEpisode = async (token: string, id: string, episode: object) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/episodes/${id}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(episode)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 删除 Episode
export const deleteEpisode = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/episodes/${id}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// AI 生成 Episode 草稿
export const generateEpisodeDraft = async (token: string, chatId: string, messages: object[]) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/episodes/generate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			chat_id: chatId,
			messages: messages
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
